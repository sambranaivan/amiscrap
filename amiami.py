from math import ceil
# import logging
from curl_cffi import requests


rootURL = "https://api.amiami.com/api/v1.0/items"
PER_PAGE = 10

class Item:
    def __init__(self, api_data):
        # Store all raw API data
        self.gcode = api_data.get('gcode')
        self.gname = api_data.get('gname')
        self.thumb_url = api_data.get('thumb_url')
        self.thumb_alt = api_data.get('thumb_alt')
        self.thumb_title = api_data.get('thumb_title')
        self.min_price = api_data.get('min_price')
        self.max_price = api_data.get('max_price')
        self.c_price_taxed = api_data.get('c_price_taxed')
        self.maker_name = api_data.get('maker_name')
        self.saleitem = api_data.get('saleitem')
        self.condition_flg = api_data.get('condition_flg')
        self.list_preorder_available = api_data.get('list_preorder_available')
        self.list_backorder_available = api_data.get('list_backorder_available')
        self.list_store_bonus = api_data.get('list_store_bonus')
        self.list_amiami_limited = api_data.get('list_amiami_limited')
        self.instock_flg = api_data.get('instock_flg')
        self.order_closed_flg = api_data.get('order_closed_flg')
        self.element_id = api_data.get('element_id')
        self.salestatus = api_data.get('salestatus')
        self.salestatus_detail = api_data.get('salestatus_detail')
        self.releasedate = api_data.get('releasedate')
        self.jancode = api_data.get('jancode')
        self.preorderitem = api_data.get('preorderitem')
        self.saletopitem = api_data.get('saletopitem')
        self.resale_flg = api_data.get('resale_flg')
        self.preowned_sale_flg = api_data.get('preowned_sale_flg')
        self.for_women_flg = api_data.get('for_women_flg')
        self.genre_moe = api_data.get('genre_moe')
        self.cate6 = api_data.get('cate6')
        self.cate7 = api_data.get('cate7')
        self.buy_flg = api_data.get('buy_flg')
        self.buy_price = api_data.get('buy_price')
        self.buy_remarks = api_data.get('buy_remarks')
        self.stock_flg = api_data.get('stock_flg')
        self.image_on = api_data.get('image_on')
        self.image_category = api_data.get('image_category')
        self.image_name = api_data.get('image_name')
        self.metaalt = api_data.get('metaalt')

    # Computed properties for backward compatibility
    @property
    def productURL(self):
        return f"https://www.amiami.com/eng/detail/?gcode={self.gcode}" if self.gcode else None

    @property
    def imageURL(self):
        return f"https://img.amiami.com{self.thumb_url}" if self.thumb_url else None

    @property
    def productName(self):
        return self.gname

    @property
    def price(self):
        return self.c_price_taxed

    @property
    def productCode(self):
        return self.gcode

    @property
    def releaseDate(self):
        return self.releasedate

    @property
    def availability(self):
        isSale = self.saleitem == 1
        isLimited = self.list_store_bonus == 1 or self.list_amiami_limited == 1
        isPreowned = self.condition_flg == 1
        isPreorder = self.preorderitem == 1
        isBackorder = self.list_backorder_available == 1
        isClosed = self.order_closed_flg == 1
        
        if isClosed:
            if isPreorder:
                return "Pre-order Closed"
            elif isBackorder:
                return "Back-order Closed"
            else:
                return "Order Closed"
        else:
            if isPreorder:
                return "Pre-order"
            elif isBackorder:
                return "Back-order"
            elif isPreowned:
                return "Pre-owned"
            elif isLimited:
                return "Limited"
            elif isSale:
                return "On Sale"
            else:
                return "Available"

    @property
    def flags(self):
        return {
            "isSale": self.saleitem == 1,
            "isLimited": self.list_store_bonus == 1 or self.list_amiami_limited == 1,
            "isPreowned": self.condition_flg == 1,
            "isPreorder": self.preorderitem == 1,
            "isBackorder": self.list_backorder_available == 1,
            "isClosed": self.order_closed_flg == 1,
        }

class ResultSet:

    def __init__(self, keyword, proxies = None):
        self.keyword = keyword
        self.proxies = proxies
        self.items = []
        self.maxItems = -1
        self.init = False
        self.currentPage = 0
        self.pages = -1
        self._itemCount = 0

    # tostring, print out item count, current page, max items, hasMore
    def __str__(self):
        return "ResultSet: itemCount={}, currentPage={}, maxItems={}, hasMore={}".format(
            self._itemCount,
            self.currentPage,
            self.maxItems,
            self.hasMore,
        )

    @property
    def hasMore(self):
        return self._itemCount < self.maxItems

    # def getNextPage(self):
    #     if self.hasMore:
    #         self.currentPage += 1
    #         return search_page(self.keyword, self.currentPage, self.proxies)
    #     else:
    #         return None

    def searchNextPage(self):
        data = {
            "s_keywords": self.keyword,
            "pagecnt": self.currentPage + 1,
            "pagemax": PER_PAGE,
            "lang": "eng",
            #"s_st_condition_flg":1,
            #"s_sortkey":"preowned"
            "s_st_list_preorder_available":1,
        }
        headers = {
            "X-User-Key": "amiami_dev",
            "User-Agent": "python-amiami_dev",
        }
        resp = requests.get(rootURL, params=data, headers=headers, impersonate="chrome110", proxies=self.proxies)
        self.__parse(resp.json())
        self.currentPage += 1


    def __add(self, productInfo):
        item = Item(productInfo)
        
        # Check for unknown status (debugging purposes)
        if item.availability == "Unknown status?":
            print("STATUS ERROR FOR {}: flags:{}, avail:{}".format(
                item.gcode,
                item.flags,
                item.availability,
            ))
        
        self.items.append(item)

    def __parse(self, obj):
        # returns true when done
        # false if can be called again
        if not self.init:
            self.maxItems = obj['search_result']['total_results']
            self.pages = int(ceil(self.maxItems / float(PER_PAGE)))
            self.init = True
        for productInfo in obj['items']:
            self.__add(productInfo)
            self._itemCount += 1

        return self._itemCount == self.maxItems

# leaving this here because I need it every time some shit breaks and don't wanna dig it up
# logging.basicConfig(
#     format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     level=logging.DEBUG
# )

def search(keywords, proxies=None):
    rs = searchPaginated(keywords=keywords, proxies=proxies)

    while rs.hasMore:
        rs.searchNextPage()

    return rs


def searchPaginated(keywords, proxies=None):
    rs = ResultSet(keyword=keywords, proxies=proxies)
    rs.searchNextPage()

    return rs

"""
def main():

   
    # Ejecutar ejemplos
    #buscar_figuras_paginado()  # Comenzamos con paginado (más rápido)
    #buscar_personajes_especificos()
    #buscar_con_proxy()
    results = searchPaginated('evangelion')
    for item in results.items:
        print(item.releaseDate)
  

if __name__ == "__main__":
    main()
"""