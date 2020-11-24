import time
from selenium import webdriver

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions

from selenium.webdriver.common.keys import Keys

from loguru import logger

from .utils import expect, expect_none


class Api(object):

    def __init__(self):

        logger.debug(f"low level initialised  chrome")

    def launch(self, driver_path):
        try:
            logger.debug(f"launching  browser {driver_path}")
            chrome_options = Options()
            #chrome_options.add_argument("--headless")
            #chrome_options.add_argument('--no-sandbox')
            self.browser = webdriver.Chrome(
                executable_path=driver_path,options=chrome_options
            )
            logger.debug(f"browser chrome launched")
        except Exception as e:
            logger.debug(f"browser error ")
            raise e
        return True

    def search_id(self, id, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_element_by_id, args=[id])

    def search_name(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_element_by_name, args=[name])

    def search_tag(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_element_by_tag_name, args=[name])

    def search_tag_array(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_elements_by_tag_name, args=[name])

    def search_class_name(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_element_by_class_name, args=[name])

    def search_class_name_array(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect(dom.find_elements_by_class_name, args=[name])

    def search_class_name_none(self, name, dom=None):
        if dom is None:
            dom = self.browser
        return expect_none(dom.find_element_by_class_name, args=[name], times=10)

    def login(self, username, password):
        url = "https://trading212.com/en/login"
        try:
            logger.debug(f"visiting %s" % url)
            self.browser.get(url)
            logger.debug(f"connected to %s" % url)
        except selenium.common.exceptions.WebDriverException:
            logger.critical("connection timed out")
            raise
        try:
            self.search_name("login[username]").send_keys(username)
            self.search_name("login[password]").send_keys(password)
            self.search_class_name("button-login").click()
            # define a timeout for logging in

            general_error = self.search_class_name_none('general-error')
            if general_error:
                logger.info(f"Login error")
                raise Exception(username)
            else:
                logger.info(f"No error, logged in as {username}")

            time.sleep(1)

        except Exception as e:
            logger.critical("login failed")
            raise e
        return True

    def logout(self):
        """logout func (quit browser)"""
        try:
            self.browser.close()
        except Exception as e:
            raise e
            return False
        logger.info("logged out")
        return True

    def get_bottom_info(self):
        result = None
        try:
            statusbar = self.search_id("statusbar")
            soup = BeautifulSoup(statusbar.get_attribute('innerHTML'), 'html.parser')
            free_founds = soup.find(id='equity-free')
            account_value = soup.find(id='equity-total')
            live_result = soup.find(id='equity-ppl')
            blocked_founds = soup.find(id='equity-blocked')

            result = {
                'free_funds': free_founds.text,
                'account_value': account_value.text,
                'live_result': live_result.text,
                'blocked_founds': blocked_founds.text}

            print(result)
        except Exception as e:
            self.handle_exception(e)
            pass
        return result

    def get_portfolio_table(self):
        try:
            table = self.search_class_name("dataTable")
            table_body = self.search_tag("tbody", dom=table)
            soup = BeautifulSoup(table_body.get_attribute('innerHTML'), 'html.parser')
            result = []

            data_codes = soup.select("tr")
            names = soup.select("td.name")
            quantities = soup.select("td.quantity")
            average_prices = soup.select("td.averagePrice")
            ppls = soup.select("td.ppl")
            prices_buy = soup.select("td.currentPrice")
            market_values = soup.select("td.marketValue")

            for index in range(len(names)):
                data_code = data_codes[index]['data-code']
                name = names[index]
                quantity = quantities[index]
                average_price = average_prices[index]
                ppl = ppls[index]
                current_price = prices_buy[index]
                current_price_text = current_price.text
                market_value = market_values[index]

                result.append({
                    "name": name.text.replace("\n", "").replace(u'\xa0', ""),
                    "data_code": data_code,
                    "quantity": quantity.text.replace("\n", "").replace(u'\xa0', ""),
                    "market_value": market_value.text.replace("\n", "").replace(u'\xa0', ""),
                    "average_price": average_price.text.replace("\n", "").replace(u'\xa0', ""),
                    "current_price": current_price_text.replace("\n", "").replace(u'\xa0', ""),
                    "profit": ppl.text.replace("\n", "").replace(u'\xa0', "")
                })


            return result
        except Exception as e:
            self.handle_exception(e)
            pass
        return []

    def _get_trade_box(self, name, data_code):
        """
        Get the trade box for selling or buying from the main window
        Args:
            name:
            data_code:

        Returns:

        """
        search_btn = self.search_class_name("search-icon")
        search_btn.click()
        time.sleep(.5)
        search_input = self.search_class_name("search-input")
        search_input.send_keys(name)
        time.sleep(.5)
        search_res = self.search_class_name("search-results")
        # search_res = trader212_broker.search_class_name('scrollable-area-content', dom=search_res)
        # instrument = search_res.find_element_by_xpath(f'//div[@data-code="{data_code}"]')
        instruments = self.search_class_name_array('search-results-instrument', dom=search_res)
        for instrument in instruments:
            if instrument.get_attribute('data-code') == data_code:
                instrument.click()

                time.sleep(.5)
                instrument_dtl = self.search_class_name('search-instrument-details')
                tradebox = self.search_class_name('invest-tradebox', dom=instrument_dtl)
                return tradebox

    def _fill_in_order(self, quantity):
        """
        fill in he order window once the buy or sell button clicked.
        it should be called only when the sell or buy button clicked
        Args:
            quantity:

        Returns:

        """

        sell_input = self.search_tag(
            "input", dom=self.search_class_name("invest-market-order")
        )

        ###### check if input accepts "."
        sell_input.send_keys(".")
        time.sleep(1)
        entered_value = sell_input.get_attribute("value")
        if "." in entered_value:
            str_quantity = "{:.2f}".format(quantity)
        else:
            str_quantity = int(quantity)

        sell_input.send_keys(Keys.BACK_SPACE)
        sell_input.send_keys(str_quantity)

        time.sleep(1)
        # button_container = self.search_class_name("tradebox-trade-container", dom=instrument)
        review_button = self.search_class_name("review-order-button")
        review_button.click()
        time.sleep(1)
        send_button = self.search_class_name("send-order-button")
        send_button.click()

        return str_quantity

    def buy(self, name, data_code, quantity):
        try:
            logger.debug(f"buy {quantity} of {name} ")
            tradebox = self._get_trade_box(name, data_code)
            buy_btn = self.search_class_name('buy-button', dom=tradebox)
            buy_btn.click()

            str_quantity = self._fill_in_order(quantity)

            logger.debug(f"bought {str_quantity} of {name}")
            time.sleep(1)
            self.browser.get("https://www.trading212.com/")
            return
        except Exception as e:
            self.handle_exception(e)
            pass

    def sell(self, name, data_code, quantity):
        try:
            logger.debug(f"buy {quantity} of {name} ")
            tradebox = self._get_trade_box(name, data_code)
            sell_btn = self.search_class_name('sell-button', dom=tradebox)
            sell_btn.click()

            str_quantity = self._fill_in_order(quantity)

            logger.debug(f"sold {str_quantity} of {name}")
            time.sleep(1)
            self.browser.get("https://www.trading212.com/")
            return
        except Exception as e:
            self.handle_exception(e)
            pass


    def handle_exception(self, exception):
        logger.critical("got exception")
        logger.critical(exception)
        # raise exception
        # send_email(exception)
