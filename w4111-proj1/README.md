Through the web implemented the functions as login and signup, search on the index page, show hotsearch, order and pay, and user can see the oder detail on his homepage.

The fun part is index and pay.
For index:we have three things shown on the page：hot_search_list，product_list，brand_list to show different type of keywords
select_sql = '''SELECT key_word,product_id FROM hotsearched WHERE searched_rank <= 10 ORDER BY searched_rank'''
select_sql = '''SELECT product_id, name, price, unit, is_shipfree FROM product WHERE isdelete = false'''
select_sql = '''SELECT DISTINCT b.brand_id, b.brand_name FROM brand b  WHERE EXISTS (SELECT * FROM product p WHERE p.brand_id=b.brand_id)'''
 
For paying: we firstly use sql to check if this user has login, if he has, we will use request form to get the information user give, and then updating our database and showing the updates on user's homepage.
