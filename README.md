# LLM-Anonymization
Method to detect and mask personally identifiable information (PII) for purposes of privacy and confidentiality.

## Development Notes
- After pulling, remember to run:
  - ```pip install -r requirements.txt``` (if libraries have changed)
  - ```python manage.py migrate```
- To run the django server: ```python manage.py runserver```
- To change database (when editing models.py): 
  - ```python manage.py makemigrations```
  - ```python manage.py migrate```
- To clear the database (in case there are conflicts): 
  - ```python manage.py flush```
  - remember to add the super user back: ```python manage.py createsuperuser```
- To collect static files
  - py manage.py collectstatic
