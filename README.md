# Product Scraper

It's small console app to scrape product information from a web page

## Expected html structure

Main page - product list

```html
<!DOCTYPE html>
<html>
<body>
    <ul class="productLister">
        <li>
            <h3>
                <a href="URL">Title</a>
            </h3>
            <tag class="pricePerUnit">£1.8/unit</tag>
        </li>
    </ul>
</body>
</html>
```

Product page - product details

```html
<!DOCTYPE html>
<html>
<body>
    <p class="productText">
        Some details about the product
    </p>
</body>
</html>
```

## Usage

Run from console with:

```bash
    python productscraper.py URL
```

Expected output

```json
{
    "total": 5.0,
    "results": [
        {
            "title": "Apricot",
            "description": "Apricots",
            "unit_price": 3.5,
            "size": "39.19kb"
        },
        {
            "title": "Avocado",
            "description": "Avocados",
            "unit_price": 1.5,
            "size": "39.60kb"
        }
    ]
}

```

## Requirements

System:

- Python 2.7+

Python packages defined in `requirements.txt`.

To install run `pip install -r requirements.txt`. Virtual environment recomanded.

## Tests

Firstly please install test requirements with `pip install -r requirements_test.txt` as well as regular requirements from `requirements.txt`.

To run them:

```
python tests.py
```