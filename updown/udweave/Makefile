

test: test-frontend test-backend
	!echo "Done running all tests"

test-frontend: test-parser test-preprocessor test-codegen
	!echo "Done running frontend tests"

test-parser:
	lit frontend/tests_parser

test-preprocessor:
	lit frontend/tests_preprocessor
    
test-codegen:
	lit frontend/tests_codegen

test-backend: 
	lit backend/test_python




