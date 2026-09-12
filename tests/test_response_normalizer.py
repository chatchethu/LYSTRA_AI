import pytest
from backend.generation.response_normalizer import (
    normalize, 
    ResponseNormalizationError,
    NovaMeta
)

def test_raw_json_never_becomes_user_content():
    raw = {
        "unknown": {
            "foo": "bar"
        }
    }
    with pytest.raises(ResponseNormalizationError):
        normalize(raw)

def test_text_json_is_normalized():
    result = normalize('{"text":"Hello!"}')
    assert result.type == "text"
    assert result.content == "Hello!"

def test_structured_blocks_are_not_flattened():
    result = normalize({
        "blocks": [
            {
                "type": "heading",
                "data": {
                    "text": "Hello"
                }
            },
            {
                "type": "table",
                "data": {
                    "columns": ["A", "B"],
                    "rows": [["1", "2"]]
                }
            }
        ]
    })

    assert result.type == "structured"
    assert result.content == ""
    assert len(result.blocks) == 2

def test_nested_envelope_unwrapped():
    result = normalize({
        "response": {
            "text": "Nested hello"
        }
    })
    assert result.type == "text"
    assert result.content == "Nested hello"

def test_blocks_without_data_envelope_fixed():
    result = normalize({
        "blocks": [
            {
                "type": "text",
                "text": "Hallucinated block structure"
            }
        ]
    })
    # 'text' should be patched into 'data.content'
    assert result.blocks[0].data["content"] == "Hallucinated block structure"

def test_nested_text_block_is_normalized():
    raw = {
        "blocks": [
            {
                "text": {
                    "content": "Roadmap for Java Learning"
                }
            }
        ]
    }
    response = normalize(raw)
    
    assert response.type == "text"
    assert response.content == "Roadmap for Java Learning"
    assert len(response.blocks) == 1
    assert response.blocks[0].type == "text"

def test_empty_response_is_rejected():
    from backend.validation.response_integrity import validate_response_integrity, ResponseValidationError
    
    raw = {
        "blocks": [
            {
                "text": {}
            }
        ]
    }
    response = normalize(raw)
    
    assert not response.content
    
    with pytest.raises(ResponseValidationError):
        validate_response_integrity(response)

def test_direct_type_data_text():
    raw = {
        "type": "text",
        "data": {
            "content": "Python NumPy is a library for numerical computing."
        },
        "metadata": {}
    }
    result = normalize(raw)
    assert result.type == "text"
    assert "NumPy" in result.content

def test_direct_type_data_structured():
    raw = {
        "type": "table",
        "data": {
            "columns": ["A"],
            "rows": [["1"]]
        },
        "metadata": {}
    }
    result = normalize(raw)
    assert result.type == "structured"
    assert len(result.blocks) == 1
    assert result.blocks[0].type == "table"
