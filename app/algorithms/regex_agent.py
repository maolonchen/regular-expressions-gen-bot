from typing import List, Dict, Any, Optional
import re
import time
import aiohttp
from app.conf.config import config
from app.api.llm_api import generate_api
from app.utils.log_utils import get_logger

try:
    from app.conf.prompts import (
        INITIAL_PROMPT_TEMPLATE,
        ADDITIONAL_EXAMPLES_SECTION,
        NEGATIVE_EXAMPLES_SECTION,
        INITIAL_PROMPT_FOOTER,
        FINAL_CHECK_TEMPLATE,
        FINAL_CHECK_ADDITIONAL,
        FINAL_CHECK_NEGATIVE,
        FINAL_CHECK_FOOTER,
        ERROR_PROMPT_HEADER,
        ERROR_PROMPT_ADDITIONAL,
        ERROR_PROMPT_NEGATIVE,
        ERROR_PROMPT_MISMATCH,
        ERROR_PROMPT_SYNTAX,
        ERROR_PROMPT_FOOTER,
        FAILURE_ANALYSIS_HEADER,
        FAILURE_ANALYSIS_FOOTER,
    )
    _PROMPTS_LOADED = True
except ImportError:
    _PROMPTS_LOADED = False

logger = get_logger(__name__)


class RegexAgent:

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _validate_regex(self, pattern: str, input_text: str) -> List[str]:
        try:
            compiled_regex = re.compile(pattern)
            match_objects = list(compiled_regex.finditer(input_text))
            matches = [match.group(0) for match in match_objects]
            match_details = [(match.group(0), match.start(), match.end()) for match in match_objects]
            logger.debug(f"Pattern '{pattern}' compiled. Matches: {matches}, Details: {match_details}")
            return matches
        except re.error as e:
            logger.error(f"Invalid pattern: {pattern}, error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error validating pattern: {e} for pattern: {pattern}")
            raise e

    def _validate_regex_with_timeout(self, pattern: str, input_text: str, timeout: float = 1.0) -> List[str]:
        try:
            start_time = time.time()
            matches = self._validate_regex(pattern, input_text)
            if time.time() - start_time > timeout:
                logger.warning(f"Execution timed out for pattern: {pattern}")
                return {"matches": [], "error": "Execution timed out"}
            return {"matches": matches, "error": None}
        except Exception as e:
            error_msg = f"Error during validation: {str(e)}"
            logger.error(error_msg)
            return {"matches": [], "error": error_msg}

    async def _call_llm(self, prompt: str) -> str:
        try:
            if not self.session:
                raise Exception("Session not initialized")
            result = await generate_api(self.session, prompt)
            return result.strip()
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise

    async def generate_regex(self, user_request: str, sample_input: str, expected_matches: List[str],
                           negative_examples: Optional[List[str]] = None,
                           additional_examples: Optional[List[str]] = None) -> Dict[str, Any]:
        attempt = 0

        if _PROMPTS_LOADED:
            initial_prompt = INITIAL_PROMPT_TEMPLATE.format(
                user_request=user_request,
                sample_input=sample_input,
                expected_matches=expected_matches,
            )
            if additional_examples:
                initial_prompt += ADDITIONAL_EXAMPLES_SECTION.format(additional_examples=additional_examples)
            if negative_examples:
                initial_prompt += NEGATIVE_EXAMPLES_SECTION.format(negative_examples=negative_examples)
            initial_prompt += INITIAL_PROMPT_FOOTER
        else:
            initial_prompt = f"Generate a Python-compatible pattern for: {user_request}\nInput: {sample_input}\nExpected: {expected_matches}\nReturn only the pattern."

        logger.debug(f"Initial prompt constructed, length={len(initial_prompt)}")

        regex = await self._call_llm(initial_prompt)
        logger.debug(f"LLM response received, length={len(regex)}")
        regex = regex.strip().strip('`').strip()
        if regex.startswith('python'):
            regex = regex[6:].strip()

        attempt_history = []

        while attempt < config.MAX_CORRECTION_ATTEMPTS:
            attempt += 1

            validation_result = self._validate_regex_with_timeout(regex, sample_input, config.MAX_EXECUTION_TIME)
            current_matches = validation_result["matches"] if validation_result["matches"] is not None else []
            regex_error = validation_result["error"]

            if regex_error:
                logger.error(f"Validation error in attempt {attempt}: {regex_error}")

            additional_matches = {}
            if additional_examples:
                for i, example in enumerate(additional_examples):
                    validation_result = self._validate_regex_with_timeout(regex, example, config.MAX_EXECUTION_TIME)
                    additional_matches[f"example_{i}"] = {
                        "input": example,
                        "matches": validation_result["matches"],
                        "error": validation_result["error"]
                    }

            negative_matches = {}
            if negative_examples:
                for i, example in enumerate(negative_examples):
                    validation_result = self._validate_regex_with_timeout(regex, example, config.MAX_EXECUTION_TIME)
                    negative_matches[f"negative_example_{i}"] = {
                        "input": example,
                        "matches": validation_result["matches"],
                        "error": validation_result["error"]
                    }

            attempt_history.append({
                "attempt": attempt,
                "regex": regex,
                "current_matches": current_matches,
                "additional_matches": additional_matches,
                "negative_matches": negative_matches,
                "error": regex_error
            })

            if set(current_matches) == set(expected_matches) and not regex_error:
                if _PROMPTS_LOADED:
                    final_check_prompt = FINAL_CHECK_TEMPLATE.format(
                        regex=regex, sample_input=sample_input,
                        current_matches=current_matches, expected_matches=expected_matches,
                    )
                    if regex_error:
                        final_check_prompt += f"Error: {regex_error}\n\n"

                    final_check_prompt += FINAL_CHECK_ADDITIONAL
                    if additional_examples:
                        for key, value in additional_matches.items():
                            final_check_prompt += f"- Input: {value['input']}\n"
                            if value['error']:
                                final_check_prompt += f"  Error: {value['error']}\n"
                            else:
                                final_check_prompt += f"  Matches: {value['matches']}\n"

                    final_check_prompt += FINAL_CHECK_NEGATIVE
                    if negative_examples:
                        for key, value in negative_matches.items():
                            final_check_prompt += f"- Input: {value['input']}\n"
                            if value['error']:
                                final_check_prompt += f"  Error: {value['error']}\n"
                            else:
                                final_check_prompt += f"  Matches: {value['matches']} (should not match)\n"

                    final_check_prompt += FINAL_CHECK_FOOTER
                else:
                    final_check_prompt = f"Pattern: {regex}\nCurrent: {current_matches}\nExpected: {expected_matches}\nEvaluate and return the pattern or a corrected one."

                logger.debug(f"Final check prompt constructed, attempt={attempt}")

                final_result = await self._call_llm(final_check_prompt)
                logger.debug(f"Final check LLM response received")
                final_result = final_result.strip().strip('`').strip()
                if final_result.startswith('python'):
                    final_result = final_result[6:].strip()

                if final_result.upper() == "CORRECT" or final_result == regex:
                    logger.info(f"Success at attempt {attempt}")
                    return {
                        "success": True,
                        "regex": regex,
                        "matches": current_matches,
                        "attempts": attempt,
                        "error": regex_error
                    }
                else:
                    regex = final_result

            # Build error correction prompt
            if _PROMPTS_LOADED:
                error_prompt = ERROR_PROMPT_HEADER.format(
                    user_request=user_request, attempt=attempt,
                    max_attempts=config.MAX_CORRECTION_ATTEMPTS,
                    regex=regex, sample_input=sample_input,
                    current_matches=current_matches, expected_matches=expected_matches,
                )
                if regex_error:
                    error_prompt += f"- Error: {regex_error}\n\n"
                else:
                    error_prompt += "\n"

                error_prompt += ERROR_PROMPT_ADDITIONAL
                if additional_examples:
                    for key, value in additional_matches.items():
                        error_prompt += f"- Input: {value['input']}\n"
                        if value['error']:
                            error_prompt += f"  Error: {value['error']}\n"
                        else:
                            error_prompt += f"  Matches: {value['matches']}\n"

                error_prompt += ERROR_PROMPT_NEGATIVE
                if negative_examples:
                    for key, value in negative_matches.items():
                        error_prompt += f"- Input: {value['input']}\n"
                        if value['error']:
                            error_prompt += f"  Error: {value['error']}\n"
                        else:
                            error_prompt += f"  Matches: {value['matches']} (should not match)\n"

                error_prompt += ERROR_PROMPT_MISMATCH.format(
                    current_matches=current_matches,
                    expected_matches=expected_matches,
                    unmatched_expected=list(set(expected_matches) - set(current_matches)),
                    unexpected_matches=list(set(current_matches) - set(expected_matches)),
                )
                if regex_error:
                    error_prompt += ERROR_PROMPT_SYNTAX.format(regex_error=regex_error)
                error_prompt += ERROR_PROMPT_FOOTER
            else:
                error_prompt = f"Attempt {attempt}/{config.MAX_CORRECTION_ATTEMPTS}\nPattern: {regex}\nCurrent: {current_matches}\nExpected: {expected_matches}\nProvide corrected pattern or CORRECT."

            logger.debug(f"Correction prompt constructed, attempt={attempt}")

            regex = await self._call_llm(error_prompt)
            logger.debug(f"Correction LLM response received")
            regex = regex.strip().strip('`').strip()
            if regex.startswith('python'):
                regex = regex[6:].strip()

            if regex.upper() == "CORRECT":
                validation_result = self._validate_regex_with_timeout(regex, sample_input, config.MAX_EXECUTION_TIME)
                current_matches = validation_result["matches"]
                regex_error = validation_result["error"]

                if set(current_matches) == set(expected_matches) and not regex_error:
                    logger.info(f"Success at attempt {attempt}")
                    return {
                        "success": True,
                        "regex": regex,
                        "matches": current_matches,
                        "attempts": attempt,
                        "error": regex_error
                    }
                else:
                    continue

        # Final attempt with full history
        if _PROMPTS_LOADED:
            failure_analysis_prompt = FAILURE_ANALYSIS_HEADER.format(
                user_request=user_request, sample_input=sample_input,
                expected_matches=expected_matches, max_attempts=config.MAX_CORRECTION_ATTEMPTS,
            )
            for hist in attempt_history:
                failure_analysis_prompt += f"\nAttempt {hist['attempt']}:\n"
                failure_analysis_prompt += f"- Pattern: {hist['regex']}\n"
                failure_analysis_prompt += f"- Main matches: {hist['current_matches']}\n"
                if hist['error']:
                    failure_analysis_prompt += f"- Error: {hist['error']}\n"
                if hist['additional_matches']:
                    failure_analysis_prompt += f"- Additional matches:\n"
                    for key, value in hist['additional_matches'].items():
                        if value['error']:
                            failure_analysis_prompt += f"  - Input: {value['input']}, Error: {value['error']}\n"
                        else:
                            failure_analysis_prompt += f"  - Input: {value['input']}, Matches: {value['matches']}\n"
                if hist['negative_matches']:
                    failure_analysis_prompt += f"- Negative matches:\n"
                    for key, value in hist['negative_matches'].items():
                        if value['error']:
                            failure_analysis_prompt += f"  - Input: {value['input']}, Error: {value['error']}\n"
                        else:
                            failure_analysis_prompt += f"  - Input: {value['input']}, Matches: {value['matches']}\n"
            failure_analysis_prompt += FAILURE_ANALYSIS_FOOTER
        else:
            failure_analysis_prompt = f"All {config.MAX_CORRECTION_ATTEMPTS} attempts failed for: {user_request}"

        try:
            final_regex = await self._call_llm(failure_analysis_prompt)
            final_regex = final_regex.strip().strip('`').strip()
            if final_regex.startswith('python'):
                final_regex = final_regex[6:].strip()

            if final_regex.upper() != "CORRECT":
                validation_result = self._validate_regex_with_timeout(final_regex, sample_input, config.MAX_EXECUTION_TIME)
                final_matches = validation_result["matches"]
                regex_error = validation_result["error"]

                return {
                    "success": not regex_error and set(final_matches) == set(expected_matches),
                    "regex": final_regex,
                    "matches": final_matches,
                    "attempts": config.MAX_CORRECTION_ATTEMPTS,
                    "error": f"Failed after {config.MAX_CORRECTION_ATTEMPTS} attempts. Last error: {regex_error}" if regex_error else f"Failed after {config.MAX_CORRECTION_ATTEMPTS} attempts."
                }
        except Exception as e:
            logger.error(f"Error during final analysis: {e}")

        last_result = attempt_history[-1] if attempt_history else {"regex": regex, "current_matches": [], "error": None}
        return {
            "success": False,
            "regex": last_result["regex"],
            "matches": last_result["current_matches"],
            "attempts": config.MAX_CORRECTION_ATTEMPTS,
            "error": f"Failed after {config.MAX_CORRECTION_ATTEMPTS} attempts. Last error: {last_result['error']}"
        }
