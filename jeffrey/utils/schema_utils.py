from typing import Set


def validate_config_parameter_is_in(
    allowed_parameter_values: Set[str],
    current_parameter_values: str,
    parameter_name: str
) -> None:
    if current_parameter_values not in allowed_parameter_values:
        raise ValueError(
            f'''
            Parameter {parameter_name} has value {current_parameter_values}.
            But, it should be one of {allowed_parameter_values}.
            '''
        )