need_exec_method = [
    'rename_function',
    'rename_variables',
]
base_method = [
    'add_exception',
    'add_arguments',
    'change_statement_order',
    'check_arguments',
    'insert_junk_function_code',
    'insert_junk_loop_code',
    'insert_unused_variables',
    'move_assignment',
    'statement_wrapping'
]
condition_transformation = [
    'add_condition',
    'div_if_else',
    'dividing_composed_if',
    'if_continue_to_if_else',
    'if_to_switch',
    'switch_if_transformation'
]

loop_transformation = [
    'div_loop',
    'for_while_transformation'
]

logic_transformation = [
    'equaivalent_arithmetic_logic',
    'equivalent_boolean_expression'
]

extract_method = [
    'extract_method_from_if',
    'extract_method_from_arithmetic',
]

arithmetic_transformation = [
    'equivalent_arithmetic_expression',
    'experession_dividing',
    'modifying_operations'
]

transformation_classification = {
    'base_method': base_method,
    'condition_transformation': condition_transformation,
    'loop_transformation': loop_transformation,
    'logic_transformation': logic_transformation,
    'arithmetic_transformation': arithmetic_transformation,
    'extract_method': extract_method
}