__author__ = 'RiteshReddy'
import __setup_path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import text
import datetime, uuid


urls = {"branch1": "mysql://root:root@localhost/compustore_branch1",
        "branch2": "mysql://root:root@localhost/compustore_branch2",
        "branch3": "mysql://root:root@localhost/compustore_branch3",
        "online": "mysql://root:root@localhost/compustore_online"}


def get_engine(to, echo=True):
    url = urls.get(to, None)
    if url is None:
        return url
    engine = create_engine(url, echo=echo)
    metadata = MetaData(bind=engine)
    return engine


def get_customers(engine=get_engine("online"), where="1"):
    return engine.execute('select * from customers WHERE ' + where).fetchall()


def make_branch_purchase(engine, laptops):
    """

    :param engine: Database engine object
    :param laptops: dictionary of laptop_ids and quantity of each => {(vendor,model) : qty}
    :return: order_id if successful, error message otherwise
    """
    connection = engine.connect()
    transaction = connection.begin()
    try:
        id = connection.execute(text("SELECT MAX(orderid) FROM `store_purchases`")).first()[0]
        if id is None:
            id = 1
        else:
            id = int(id) + 1
        insert_purchase = text("INSERT INTO `store_purchases` (`orderid`, `purchase_date`) VALUES(:id, :date)")
        connection.execute(insert_purchase, {"id": str(id), "date": datetime.date.today().isoformat()})
        for laptop, qty in laptops.items():
            insert_line_item = text(
                "INSERT INTO `line_item` (`vendor`, `model`, `orderid`, `quantity`) VALUES (:vendor, :model, :orderid, :quantity)")
            connection.execute(insert_line_item,
                               {'vendor': laptop[0], 'model': laptop[1], 'orderid': id, 'quantity': qty})
            connection.execute(text(
                "UPDATE `inventory` SET `quantity` = `quantity` - :quantity WHERE `vendor`=:vendor and `model`=:model"),
                               {'quantity': qty, "vendor": laptop[0], "model": laptop[1]})
        transaction.commit()
        return id, None
    except Exception, e:
        transaction.rollback()
        return None, e.message


def make_online_purchase(customer_id, laptops):
    """

    :param engine: Connection engine
    :param customer_id: customer purchasing this item
    :param laptops: dictionary of laptops -> qty + branch => {(vendor, model):(qty, branch)}
    :return: order_id, tracking_id
    """
    connections = {}
    transactions = {}
    for id in urls.keys():
        connections[id] = get_engine(id).connect()
        transactions[id] = connections[id].begin()
    try:
        id = connections['online'].execute(text("SELECT MAX(orderid) FROM `online_purchases`")).first()[0]
        if id is None:
            id = 1
        else:
            id = int(id) + 1
        trackingno = str(uuid.uuid4())
        insert_purchase = text(
            "INSERT INTO `online_purchases` (`orderid`, `purchase_date`, `trackingno`, `custid`) VALUES(:id, :date, :trackingno, :custid)")
        connections['online'].execute(insert_purchase, {"id": str(id), "date": datetime.date.today().isoformat(),
                                                        "trackingno": trackingno, "custid": customer_id})
        for laptop, details in laptops.items():
            insert_line_item = text(
                "INSERT INTO `line_item` (`vendor`, `model`, `orderid`, `quantity`, `branch_id`) VALUES (:vendor, :model, :orderid, :quantity, :branch_id)")
            connections['online'].execute(insert_line_item, {'vendor': laptop[0], 'model': laptop[1], 'orderid': id,
                                                             'quantity': details[0], "branch_id": details[1]})
            connections[details[1]].execute(text(
                "UPDATE `inventory` SET `quantity` = `quantity` - :quantity WHERE `vendor`=:vendor and `model`=:model"),
                                            {'quantity': details[0], "vendor": laptop[0], "model": laptop[1]})
        for transaction in transactions.values():
            transaction.commit()
        return id, trackingno
    except Exception, e:
        for transaction in transactions.values():
            transaction.rollback()
        return None, e


def test_make_branch_purchase():
    engine = get_engine("branch1")
    print make_branch_purchase(engine, {('Acer', '00CA'): 2, ('Acer', '00H'): 1})


def text_make_online_purchase():
    print make_online_purchase("1", {('Acer', '00CA'): (2, 'branch1'), ('Acer', '00H'): (1, 'branch1'),
                                     ('Acer', '0071'): (1, 'branch2')})


if __name__ == "__main__":
    test_make_branch_purchase()
    text_make_online_purchase()