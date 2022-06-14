import json
from api_functions import get_url_content


def get_op_response(url):
    response = get_url_content(url)
    document_data = json.loads(response.text)
    if document_data['meta']['results']['count'] > 0:
        return True
    else:
        return False