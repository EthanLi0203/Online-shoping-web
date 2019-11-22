# Online-shoping-web

This is a online shopping website written by flask, and through which the web app implemented the functions such as login and signup, searching on the index page, showing hotsearch, order and pay. Furthermore, the users are able to see the oder detail on his homepage as well.

The fun part is index and pay. For index:we have three things shown on the page：hot_search_list，product_list，brand_list to show different type of keywords select_sql = '''SELECT key_word,product_id FROM hotsearched WHERE searched_rank <= 10 ORDER BY searched_rank''' select_sql = '''SELECT product_id, name, price, unit, is_shipfree FROM product WHERE isdelete = false''' select_sql = '''SELECT DISTINCT b.brand_id, b.brand_name FROM brand b WHERE EXISTS (SELECT * FROM product p WHERE p.brand_id=b.brand_id)'''

Regarding the paying part: we firstly used sql to check if this user has loged in, if he has then we will use request form to get the information user give, and then updating our database and showing the updates on user's homepage.
