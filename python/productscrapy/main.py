import scrapy, json

class GenericProductSpider(scrapy.Spider):
    name = "generic_product"

    def __init__(self, site, sku, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("sites.json") as f:
            self.config = json.load(f)[site]
        self.sku = sku
        self.start_urls = [self.config["search_url"].format(sku=sku)]

    def parse(self, response):
        product_url = response.css(self.config["product_link"]).get()
        if product_url:
            yield response.follow(product_url, callback=self.parse_product)

    def parse_product(self, response):
        desc = response.css(self.config["description_selector"]).get()
        yield {"sku": self.sku, "description": desc, "url": response.url}
