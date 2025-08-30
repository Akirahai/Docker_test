from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer.entities import OperatorConfig
from presidio_analyzer.nlp_engine import TransformersNlpEngine, NerModelConfiguration
from transformers import AutoTokenizer, AutoModelForTokenClassification
# transformers_model = "dslim/bert-base-NER"
transformers_model = "StanfordAIMI/stanford-deidentifier-base"

# Transformer model config
model_config = [
    {"lang_code": "en",
     "model_name": {
         "spacy": "en_core_web_sm", # for tokenization, lemmatization
         "transformers": transformers_model # for NER
    }
}]

# Entity mappings between the model's and Presidio's
mapping = dict(
    PER="PERSON",
    LOC="LOCATION",
    ORG="ORGANIZATION",
    AGE="AGE",
    ID="ID",
    EMAIL="EMAIL",
    DATE="DATE_TIME",
    PHONE="PHONE_NUMBER",
    PERSON="PERSON",
    LOCATION="LOCATION",
    GPE="LOCATION",
    ORGANIZATION="ORGANIZATION",
    NORP="NRP",
    PATIENT="PERSON",
    STAFF="PERSON",
    HOSP="LOCATION",
    PATORG="ORGANIZATION",
    TIME="DATE_TIME",
    HCW="PERSON",
    HOSPITAL="LOCATION",
    FACILITY="LOCATION",
    VENDOR="ORGANIZATION",
)

labels_to_ignore = ["O"]

ner_model_configuration = NerModelConfiguration(
    model_to_presidio_entity_mapping=mapping,
    alignment_mode="expand", # "strict", "contract", "expand"
    aggregation_strategy="max", # "simple", "first", "average", "max"
    labels_to_ignore = labels_to_ignore)

transformers_nlp_engine = TransformersNlpEngine(
    models=model_config,
    ner_model_configuration=ner_model_configuration)

# Transformer-based analyzer
analyzer = AnalyzerEngine(
    nlp_engine=transformers_nlp_engine, 
    supported_languages=["en"]
)


# Initialize Presidio engines once
anonymizer = AnonymizerEngine()
analyzer = AnalyzerEngine()

# Custom replacement values for each entity type
ENTITY_REPLACEMENTS = {
    "PERSON": "ABC",
    "PHONE_NUMBER": "0000000",
    "EMAIL_ADDRESS": "example@gmail.com",
    "US_SSN": "000-00-0000",
    "CREDIT_CARD": "0000-0000-0000-0000",
    "IP_ADDRESS": "192.168.1.1",
    "LOCATION": "Anytown",
    "URL": "https://example.com",
    "DATE_TIME": "2023-01-01",
    "CRYPTO": "abc123",
    "US_PASSPORT": "000000000",
    "US_BANK_NUMBER": "000000000",
    "US_DRIVER_LICENSE": "D000000000",
    "IBAN_CODE": "GB00 0000 0000 0000 0000 00",
    "UK_NHS": "000 000 0000",
    "US_ITIN": "000-00-0000",
    "MEDICAL_LICENSE": "ML000000",
    "NRP": "000000000"
}

FULL_ENTITIES = ['CRYPTO', 'US_PASSPORT', 'DATE_TIME', 'EMAIL_ADDRESS', 'URL', 'US_BANK_NUMBER', 'US_DRIVER_LICENSE', 'IBAN_CODE', 'UK_NHS', 'US_ITIN', 'CREDIT_CARD', 'IP_ADDRESS', 'PERSON', 'PHONE_NUMBER', 'MEDICAL_LICENSE', 'US_SSN', 'LOCATION', 'NRP']


def presidio_anonymize(data: dict, use_custom_replacements: bool = False) -> dict:
    """
    Anonymize sensitive information sent by the user or returned by the model.
    Works for structures with either:
      - {"messages":[{role, content}, ...]}
      - {"choices":[{"message":{role, content}}, ...]}
    
    Args:
        data: The input data containing messages or choices
        use_custom_replacements: If True, uses custom replacement values. If False, uses default <ENTITY_TYPE> format
    """
    message_list = (
        data.get("messages") or [data.get("choices", [{}])[0].get("message")]
    )

    if not message_list or not all(isinstance(msg, dict) and msg for msg in message_list):
        return data

    for message in message_list:
        content = message.get("content", "")
        if not content.strip():
            continue

        results = analyzer.analyze(
            text=content,
            entities= FULL_ENTITIES,
            language="en",
        )
        
        if use_custom_replacements:
            # Create operator configs for custom replacements
            operators = {}
            for result in results:
                entity_type = result.entity_type
                if entity_type in ENTITY_REPLACEMENTS:
                    operators[entity_type] = OperatorConfig("replace", {"new_value": ENTITY_REPLACEMENTS[entity_type]})
            
            anonymized_result = anonymizer.anonymize(
                text=content,
                analyzer_results=results,
                operators=operators,
            )
        else:
            # Use default masking (<ENTITY_TYPE> format)
            anonymized_result = anonymizer.anonymize(
                text=content,
                analyzer_results=results,
            )
        
        message["content"] = anonymized_result.text

    return data