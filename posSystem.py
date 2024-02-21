# Imports
import sqlite3
import statistics
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime, timedelta

# Setup
con = sqlite3.connect("POS.db")
cur = con.cursor()

# Main
def main():
    # Display the log in screen
    loggedIn = logIn()
    
    # Show menu
    valid = ['a', 'b', 'c', 'd', 'e']
    logOut = False
    while not logOut:
        # Get selection
        print("\n\tMenu")
        print("-" * 35)
        print("\n\ta) Purchase")
        print("\tb) Time Clock")
        print("\tc) Dashboard")
        print("\td) Admin")
        print("\te) Logout")
        selection = input("\t=> ")
        # Validate
        while selection not in valid:
            selection = input("\t=> ")
        match selection:
            case 'a': 
                purchase()
            case 'b':
                timeClock()
            case 'c':
                dashboard()
            case 'd':
                admin()
            case 'e':
                logOut = True
    cur.close()
    con.close()

# Log in function
def logIn():
    loggedIn = False
    while not loggedIn:
        # Get username and password
        print("LOG IN")
        print("-" * 6)
        username = input("Username: ")
        password = input("Password: ")
        
        # Connect to db and log in if possible
        cur.execute("SELECT first_name, last_name, emp_id FROM Employee")
        returnVal = cur.fetchall()
        for employee in returnVal:
            if username == "" or password == "":
                loggedIn = False
            # Check first letter, lastname, and employee id
            elif employee[0][0].lower() == username[0] and employee[0][0].lower() == password[0] and employee[1].lower() == username[1:] and password[1:(len(password) - len(str(employee[2])))] == employee[1].lower() and password[(len(password) - len(str(employee[2]))):] == str(employee[2]).lower():
                loggedIn = True
        if not loggedIn:
            print("\nACCESS DENIED\n")
    return loggedIn

# Purchase Function
def purchase():
    curEmployee = getEmpIdFromUser()
    
    # Get valid product id's with matching into 
    addedProducts = []
    doneAdding = False
    order = []
    errorMessage = ""
    total = 0
    
    while not doneAdding:
        # Display screen
        print("\n\tOrder:")
        print("-" * 35)
        for item in order:
            print(item)
        # if errorMessage != "":
        print(errorMessage)
        print(f"\tTotal: {total:.2f}")
        print("\nenter \"d\" when finished")
        print("-" * 35)

        # Add item
        pId = input("product id => ")
        if pId != 'd':
            cur.execute("SELECT product_id, price, name, quantity FROM Product WHERE product_id = (?)", (pId,))
            product = cur.fetchmany()

            if len(product) != 0:
                # Get Quantity
                validQuantity = False
                while not validQuantity:
                    try:
                        quantity = int(input("quantity => "))
                        validQuantity = True
                    except:
                        validQuantity = False

                # Check to see if it is already in order
                prevAdded = False
                prevQuantity = 0
                total += (product[0][1] * quantity)
                for i in range(len(addedProducts)):
                    if str(addedProducts[i][0]) == pId:
                        prevAdded = True
                        # Add the quantity it had
                        quantity += addedProducts[i][1]
                        # Update the added products
                        addedProducts[i][1] = quantity
                        # Find it in the order
                        for j in range(len(order)):
                            if order[j][0:len(str(pId))] == pId:
                                order[j] = "{:<4} {:<20} {:<4} {:<5}\n".format(product[0][0], product[0][2], quantity, (product[0][1] * quantity))
                
                if not prevAdded:
                    order.append("{:<4} {:<20} {:<4} {:<5}\n".format(product[0][0], product[0][2], quantity, (product[0][1] * quantity)))
                    addedProducts.append([product[0][0], quantity, product[0][1]])
                errorMessage = ""
            else:
                errorMessage = "invalid product id"
        else:
            # Confirm purchase
            completePurchase = input("Complete purchase (y / n) => ")
            if completePurchase.lower() == 'y':
                doneAdding = True
                if len(addedProducts) != 0:
                    orderId = addNewOrder(curEmployee, addedProducts, total)
                    print(f"\tOrder Number: {orderId}")

# Function to update database when an order is made
def addNewOrder(empId, addedProducts, total):
    # Add new order to order
    # Current date from https://www.programiz.com/python-programming/datetime/current-datetime
    cur.execute("INSERT INTO Orders (order_date, total_price, emp_id) values (?,?,?)", (date.today().strftime("%m/%d/%Y"), total, empId))

    # Get the order id from https://www.sliqtools.co.uk/blog/technical/sqlite-how-to-get-the-id-when-inserting-a-row-into-a-table/
    cur.execute("SELECT last_insert_rowid()")
    orderNum = cur.fetchall()[0][0]

    # Add new order to product order and subtract quantity
    # For item in added products
    for item in addedProducts:
        # INSERT INTO OrderProducts (order_id, product_id, quantity, total) values (?,?)
        cur.execute("INSERT INTO OrderProducts (order_id, product_id, quantity, total) values (?,?,?,?)", (orderNum, item[0], item[1], (item[2] * item[1])))
        # Get the new quantity
        cur.execute("SELECT quantity FROM Product WHERE product_id = (?)", (item[0],))
        newQuantity = cur.fetchall()[0][0] - item[1]
        # Update
        cur.execute("UPDATE Product SET quantity = (?) WHERE product_id = (?)", (newQuantity, item[0]))

    # Commit all changes
    con.commit()
    # Return the order number
    return orderNum

# Helper function to get emp_id from a username
def getEmpIdFromUser():
    # Get username for userID
    matched = False
    username = input("Enter employee username: ")
    # TODO Make better?
    cur.execute("SELECT first_name, last_name, emp_id FROM Employee")
    returnVal = cur.fetchall()
    while not matched:
        for employee in returnVal:
            if username != "":
                if employee[0][0].lower() == username[0] and employee[1].lower() == username[1:]:
                    matched = True
                    curEmployee = employee[2]
        if not matched:
            username = input("Invalid username: ")
    return curEmployee

# Time clock function to clock workers in and out
def timeClock():
    # Get emp_id from username
    empId = getEmpIdFromUser()

    cur.execute("SELECT last_clocked_in, hours_in_period, total_hours_worked FROM EmployeeHours WHERE emp_id = (?)", (empId,))
    returnVal = cur.fetchall()
    # If last clocked in is NULL, clock them in
    if returnVal[0][0] == None:
        cur.execute("UPDATE EmployeeHours SET last_clocked_in = (?) WHERE emp_id = (?)", (str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), empId))
        # Create print message
        cur.execute("SELECT first_name, last_name FROM Employee WHERE emp_id = (?)", (empId,))
        name = cur.fetchall()
        print(f"{name[0][0]} {name[0][1]} clocked in")
    else:
        # Find time worked
        # From https://www.datacamp.com/tutorial/converting-strings-datetime-objects
        timeWorked = datetime.now() - datetime.strptime(returnVal[0][0], "%Y-%m-%d %H:%M:%S")
        hoursWorked = timeWorked.total_seconds() / 3600.0
    # Add time worked to their hours worked in total and in pay period and set clocked in to NULL
        cur.execute("UPDATE EmployeeHours SET last_clocked_in = (?), hours_in_period = (?) ,total_hours_worked = (?) WHERE emp_id = (?)", (None, (returnVal[0][1] + hoursWorked), (returnVal[0][2] + hoursWorked), empId))
    # Print that they were clocked out
        cur.execute("SELECT first_name, last_name FROM Employee WHERE emp_id = (?)", (empId,))
        name = cur.fetchall()
        print(f"{name[0][0]} {name[0][1]} clocked out with {hoursWorked:.2f} hours")
    con.commit()

def dashboard():
    # Valid options
    validOptions = ['a', 'b', 'c', 'd']
    # Get user option
    print("\nDashboard:")
    print("-" * 30)
    print("\ta) Product Query")
    print("\tb) Order Query")
    print("\tc) Sales Visualization")
    print("\td) Inventory Inquiry")
    selection = input("\t=> ")
    while selection not in validOptions:
        selection = input("Invalid Option => ")
    # Product Query
    if selection == 'a':
        productQuery()
    # Order Query
    elif selection == 'b':
        orderQuery()
    # Sales Visualization
    elif selection == 'c':
        dataVis()
    else:
        inventory()

def productQuery():
    # Set valid columns and queries
    validNumColumns = ["product_id", "price", "quantity"]
    validOtherColumns = ["category", "name", "*"]
    validNumQueries = ["avg", "min", "max", "median", "std deviation"]
    whereColumn = None
    mathQuery = False

    # Show user valid columns 
    print("Valid Columns: ", end=" ")
    for item in validNumColumns:
        print(item, end=", ")
    for item in validOtherColumns:
        print(item, end=", ")
    # Get user selection
    selectedColumn = input("\nWrite column name to query => ").lower()
    while selectedColumn not in validNumColumns and selectedColumn not in validOtherColumns:
        selectedColumn = input("Invalid Column. Write column name to query => ").lower()
    
    # Go down proper numerical or WHERE path
    if selectedColumn in validNumColumns:
        mathQuery = True;
        # Find mean, min, max
        print("Valid Queries: ", end=" ")
        for item in validNumQueries:
            print(item, end=", ")
        selectedQuery = input("\nWrite query => ").lower()
        while selectedQuery not in validNumQueries:
            selectedQuery = input("Invalid Column. Write query => ").lower()
        
        # Ask if they want to add a where
        if input("Add a where restriction? (y / n) => ") == 'y':
            print("Valid Columns: ", end=" ")
            for item in validNumColumns:
                print(item, end=", ")
            for item in validOtherColumns:
                print(item, end=", ")
            # Get user selection
            whereColumn = input("\nWrite column to restrict => ").lower()
            while whereColumn not in validNumColumns and selectedColumn not in validOtherColumns:
                whereColumn = input("Invalid Column. Write column to restrict => ").lower()
            # Get restriction
            restriction = input(f"Filter where {whereColumn} = ")

        # Write query
        if selectedQuery == "median" or selectedQuery == "std deviation":
            # Get all values
            queryStr = f"SELECT {selectedColumn} FROM Product"
        else:
            queryStr = f"SELECT {selectedQuery}({selectedColumn}) FROM Product"
        if whereColumn != None:
            queryStr += f" WHERE {whereColumn} = {restriction}"
    else:
        if input("Add a where restriction? (y / n) => ") == 'y':
            print("Valid Columns: ", end=" ")
            for item in validNumColumns:
                print(item, end=", ")
            for item in validOtherColumns:
                print(item, end=", ")
            # Get user selection
            whereColumn = input("\nWrite column to restrict => ").lower()
            while whereColumn not in validNumColumns and selectedColumn not in validOtherColumns:
                whereColumn = input("Invalid Column. Write column to restrict => ").lower()
            # Get restriction
            restriction = input(f"Filter where {whereColumn} = ")
        
        # Write Query
        queryStr = f"SELECT {selectedColumn} from Product"
        if whereColumn != None:
            queryStr += f" WHERE {whereColumn} = '{restriction}'"
    
    # Complete Query
    cur.execute(queryStr)
    returnVal = cur.fetchall()
    if mathQuery:
        if selectedQuery == "std deviation":
            # From https://www.w3schools.com/python/ref_stat_stdev.asp#:~:text=stdev()%20method%20calculates%20the,clustered%20closely%20around%20the%20mean.
            # Calculate std dev in python
            data = []
            for item in returnVal:
                data.append(item[0])
            stdDev = statistics.stdev(data)
            print(f"\n{selectedColumn} {selectedQuery}: {stdDev:.2f}")
        elif selectedQuery == "median":
            # From https://www.w3schools.com/python/ref_stat_median.asp#:~:text=The%20statistics.,in%20a%20set%20of%20data.
            # Calculate median in python
            data = []
            for item in returnVal:
                data.append(item[0])
            median = statistics.median(data)
            print(f"\n{selectedColumn} {selectedQuery}: {median}")
        else:
            print(f"\n{selectedColumn} {selectedQuery}: {returnVal[0][0]:.2f}")
    else:
        printRow = ""
        for row in returnVal:
            for item in row:
                printRow += "{:<15}".format(item)
            printRow += "\n"
        print(f"\n{printRow}")

def orderQuery():
    # Get user selection for general or specific order query
    validOptions = ['a', 'b']
    whereColumn = None
    mathQuery = False
    print("\nWhat would you like to query?")
    print("\ta) General Orders")
    print("\tb) Specific Order")
    selection = input('\t=> ')
    # Validate
    while selection not in validOptions:
        selection = input('\tInvalid option => ')
    
    if selection == 'a':
        genOrderColumns = ['order_id', 'order_date', 'total_price', 'emp_id', '*']
        # Get user column selection
        print("Valid Columns: ", end="")
        for column in genOrderColumns:
            print(f"{column}", end=", ")
        selectedColumn = input("\nWrite column name to query => ")
        while selectedColumn not in genOrderColumns:
            selectedColumn = input("\Invalid column name to query => ")

        # If total price, then let numeric queries
        if selectedColumn == 'total_price':
            mathQuery = True
            validNumQueries = ["avg", "min", "max", "median", "std deviation"]
            print("Valid Queries: ", end="")
            for query in validNumQueries:
                print(f"{query}", end=", ")
            selectedQuery = input("\nWrite query => ")
            while selectedQuery not in validNumQueries:
                selectedQuery = input("Invalid query => ")

            # Ask to add where
            if input("Add a where restriction? (y / n) => ") == 'y':
                print("Valid Columns: ", end=" ")
                for item in genOrderColumns:
                    print(item, end=", ")
                # Get user selection
                whereColumn = input("\nWrite column to restrict => ").lower()
                while whereColumn not in genOrderColumns:
                    whereColumn = input("Invalid Column. Write column to restrict => ").lower()
                # Get restriction
                restriction = input(f"Filter where {whereColumn} = ")
                queryStr = f"SELECT {selectedColumn} FROM Orders"
                if whereColumn != None:
                    queryStr += f" WHERE {whereColumn} = {restriction}"
            
            # Write query
            if selectedQuery == "std deviation" or selectedQuery == "median":
                queryStr = f"SELECT {selectedColumn} FROM Orders"
            else:
                queryStr = f"SELECT {selectedQuery}({selectedColumn}) FROM Orders"
        else:
            # Ask to add where
            if input("Add a where restriction? (y / n) => ") == 'y':
                print("Valid Columns: ", end=" ")
                for item in genOrderColumns:
                    print(item, end=", ")
                # Get user selection
                whereColumn = input("\nWrite column to restrict => ").lower()
                while whereColumn not in genOrderColumns:
                    whereColumn = input("Invalid Column. Write column to restrict => ").lower()
                # Get restriction
                restriction = input(f"Filter where {whereColumn} = ")
            queryStr = f"SELECT {selectedColumn} FROM Orders"
            if whereColumn != None:
                queryStr += f" WHERE {whereColumn} = '{restriction}'"
        
        # Complete Query
        cur.execute(queryStr)
        returnVal = cur.fetchall()
        if mathQuery:
            if selectedQuery == "std deviation":
                # Calculate std dev
                data = []
                for item in returnVal:
                    data.append(item[0])
                stdDev= statistics.stdev(data)
                print(f"\n{selectedColumn} {selectedQuery}: {stdDev:2f}")
            elif selectedQuery == "median":
                # Calculate median
                data = []
                for item in returnVal:
                    data.append(item[0])
                median = statistics.median(data)
                print(f"\n{selectedColumn} {selectedQuery}: {median}")
            else:
                print(f"\n{selectedColumn} {selectedQuery}: {returnVal[0][0]:.2f}")
        else:
            printRow = ""
            for row in returnVal:
                for item in row:
                    printRow += "{:<15}".format(item)
                printRow += "\n"
            print(f"\n{printRow}")
    else:
        validNumColumns = ['Orders.order_id', 'Orders.total_price', 'Orders.emp_id', 'OrderProducts.product_id', 'OrderProducts.quantity', 'OrderProducts.total']
        # Either get specific order or get other
        if (input("Filter by specific order (y / n) => ") == 'y'):
            validColumns = ['order_date', 'total_price', 'emp_id', 'product_id', 'quantity']
            # Get valid order number 
            validNumber = False
            while not validNumber:
                try:
                    orderNum = int(input("Enter order number => "))
                    validNumber = True
                except:
                    print("Invalid. Enter an integer")
            
            whereColumn = None
            # Ask to add where
            if input("Add a where restriction? (y / n) => ") == 'y':
                print("Valid Columns: ", end=" ")
                for item in validColumns:
                    print(item, end=", ")
                # Get user selection
                whereColumn = input("\nWrite column to restrict => ").lower()
                while whereColumn not in validColumns:
                    whereColumn = input("Invalid Column. Write column to restrict => ").lower()
                # Get restriction
                restriction = input(f"Filter where {whereColumn} = ")
            
            # Write query
            queryStr = f'''SELECT Orders.order_id, Orders.order_date, Orders.total_price,
                           Orders.emp_id, OrderProducts.product_id, OrderProducts.quantity, 
                           OrderProducts.total, Product.name FROM Orders JOIN OrderProducts on 
                           Orders.order_id == OrderProducts.order_id Join Product on 
                           OrderProducts.product_id = Product.product_id WHERE 
                           Orders.order_id = {orderNum}'''
            if whereColumn != None:
                if whereColumn in validNumColumns:
                    queryStr += f" AND Orders.{whereColumn} = {restriction}"
                else:
                    queryStr += f" AND Orders.{whereColumn} = '{restriction}'"

            # Execute and display
            cur.execute(queryStr)
            returnVal = cur.fetchall()
            print("\nnum|date      |total |emp_id|p_id|amt|subtotal|name")
            print("-" * 61)
            for row in returnVal:
                print(f"{row[0]:<3} {row[1]:<10} ${row[2]:<8} {row[3]:<4} {row[4]:<3} {row[5]:<2} ${row[6]:<7} {row[7][:15]:<15}")
        else:
            validNumQueries = ["avg", "min", "max", "median", "std deviation"]
            print("Valid columns: ", end="")
            for column in validNumColumns:
                print(column, end=", ")
            # Get user column
            selectedColumn = input("\n\tSelect a column => ")
            while selectedColumn not in validNumColumns:
                selectedColumn = input("Invalid. Select a column => ")
            # Get query
            print("Valid columns: ", end="")
            for column in validNumQueries:
                print(column, end=", ")
            # Get user column
            selectedQuery = input("\t\nSelect a query => ")
            while selectedQuery not in validNumQueries:
                selectedQuery = input("Invalid. Select a query => ")
            
            # Ask to add where
            whereColumn = None
            if input("Add where restriction? (y / n) => ") == 'y':
                # Get user column to restrict
                print("Valid columns: ", end="")
                for column in validNumColumns:
                    print(column, end=", ")
                whereColumn = input("\n\tSelect column to restrict => ")
                while whereColumn not in validNumColumns:
                    whereColumn = input("Invalid. Select column to restrict => ")
            
                # Get restriction
                restriction = input(f"Restrict where {whereColumn} = ")

            # Write query
            if selectedQuery == "std deviation" or selectedQuery == "median":
                queryStr = f'''SELECT {selectedColumn} FROM 
                           Orders JOIN OrderProducts on Orders.order_id == OrderProducts.order_id 
                           Join Product on OrderProducts.product_id = Product.product_id'''
            else:
                queryStr = f'''SELECT {selectedQuery}({selectedColumn}) FROM 
                            Orders JOIN OrderProducts on Orders.order_id == OrderProducts.order_id 
                           Join Product on OrderProducts.product_id = Product.product_id'''
            if whereColumn != None:
                if whereColumn in validNumColumns:
                    queryStr += f" WHERE {whereColumn} = {restriction}"
                else:
                    queryStr += f" WHERE {whereColumn} = '{restriction}'"
            
            # Execute query
            cur.execute(queryStr)
            returnVal = cur.fetchall()

            # Print value
            if selectedQuery == "std deviation":
                # Calculate
                data = []
                for item in returnVal:
                    data.append(item[0])
                stdDev = statistics.stdev(data)
                print(f"\n{selectedColumn} {selectedQuery}: {stdDev:.2f}")
            elif selectedQuery == "median":
                # Calculate
                data = []
                for item in returnVal:
                    data.append(item[0])
                median = statistics.median(data)
                print(f"\n{selectedColumn} {selectedQuery}: {median}")
            else:
                print(f"\n{selectedColumn} {selectedQuery}: {returnVal[0][0]}")

def dataVis():
    # Get menu option
    validOptions = ['a', 'b', 'c']
    print("\n\ta) Employee Sales")
    print("\tb) Total sales")
    print("\tc) Inventory")
    selection = input("Pick a data visualization => ")
    while selection not in  validOptions:
        selection = input("Invalid. Pick a data visualization => ")
    
    # Go down proper data visualization
    if selection == "a":
        # Get data
        cur.execute('''SELECT Employee.first_name, Employee.last_name, count(Orders.order_id) FROM Employee JOIN Orders on 
                    Employee.emp_id = Orders.emp_id GROUP BY Employee.emp_id ORDER BY count(Orders.order_id) DESC''')
        returnVal = cur.fetchall()
        # Put x and y data into 
        xAxis = []
        yAxis = []
        for item in returnVal:
            xAxis.append(f"{item[0]} {item[1]}")
            yAxis.append(item[2])
        # Set up plot
        plt.bar(xAxis, yAxis)
        plt.xlabel("Employee Name")
        plt.ylabel("Number of Sales")
        plt.title("Employee Sales")

        # Show the plot
        plt.show()
    elif selection == "b":
        validTime = ["all time", "year", "30 days", "week"]
        curTime = datetime.now()
        for time in validTime:
            print(time, end=", ")
        timeSelection = input("\nPick a time period => ")
        while timeSelection not in validTime:
            timeSelection = input("Invalid. Pick a time period => ")
        # Go down proper time selection
        queryStr = '''SELECT Orders.order_date, count(Orders.order_id) FROM Orders'''
        if timeSelection == "year":
            yearAgo = curTime - timedelta(days=365)
            yearAgoStr = yearAgo.strftime("%m/%d/%Y")
            # Add where
            queryStr += f" WHERE Orders.order_date > '{yearAgoStr}'"
        elif timeSelection == "30 days":
            monthAgo = curTime - timedelta(days=30)
            monthAgoStr = monthAgo.strftime("%m/%d/%Y")
            # Add where
            queryStr += f" WHERE Orders.order_date > '{monthAgoStr}'"
        elif timeSelection == "week":
            weekAgo = curTime - timedelta(days=7)
            weekAgoStr = weekAgo.strftime("%m/%d/%Y")
            # Add where
            queryStr += f" WHERE Orders.order_date > '{weekAgoStr}'"
        # Execute query
        queryStr += " GROUP BY Orders.order_date ORDER BY Orders.order_date"
        cur.execute(queryStr)
        returnVal = cur.fetchall()

        # Make axis
        xAxis = []
        yAxis = []

        # Fill axis
        for item in returnVal:
            xAxis.append(item[0])
            yAxis.append(item[1])

        # Make plot
        plt.bar(xAxis, yAxis)
        plt.xlabel("Day")
        plt.ylabel("Number of Sales")
        plt.title(f"{timeSelection} sales")

        # Display
        plt.show()
    elif selection == "c":
        # Get data
        cur.execute("SELECT product_id, quantity FROM Product ORDER BY product_id ASC")
        returnVal = cur.fetchall()
        
        # Set up axis
        xAxis = []
        yAxis = []
        for item in returnVal:
            xAxis.append(str(item[0]))
            yAxis.append(item[1])
        
        # Make plot
        plt.bar(xAxis, yAxis)
        plt.xlabel("Product ID")
        plt.ylabel("Quantity")
        plt.title("Store Inventory")

        # Show plot
        plt.show()

def inventory():
    # Get product id
    pId = input("Enter product ID => ")

    # Get info and quantity
    cur.execute("SELECT product_id, price, category, name, quantity FROM Product WHERE product_id = (?)", (pId,))
    returnVal = cur.fetchall()

    # Display to user
    print("\npID |price   |category            |name                |quantity")
    print("-" * 63)
    for row in returnVal:
        print(f"{row[0]:<4} {row[1]:<8} {row[2][:20]:<20} {row[3][:20]:<20} {row[4]:<4}")

def admin():
    # Make sure they have manager status
    curEmp = getEmpIdFromUser()
    cur.execute("SELECT active, manager FROM Employee WHERE emp_id = (?)", (curEmp,))
    returnVal = cur.fetchall()

    # Access only if active manager
    if (returnVal[0][0] == 1 and returnVal[0][1] == 1):
        validOptions = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        # Print menu
        print("\nAdmin")
        print("-" * 30)
        print("\ta) Update product information")
        print("\tb) Add new product")
        print("\tc) Update employee information")
        print("\td) Add employee")
        print("\te) Employee Query")
        print("\tf) View employee hours")
        print("\tg) Payroll")
        print("\th) Remove entity from table")

        # Get and validate user input
        selection = input("\t=> ")
        while selection not in validOptions:
            selection = input("Invalid => ")
        
        # Call proper function
        if selection == "a":
            updateProductInfo()
        elif selection == "b":
            addNewProduct()
        elif selection == "c":
            updateEmpInfo()
        elif selection == "d":
            addEmp()
        elif selection == "e":
            empQuery()
        elif selection == "f":
            viewHours()
        elif selection == "g":
            payroll()
        else:
            removeFromTable()
    # Reject access
    else:
        print("You do not have access to admin")

def updateProductInfo():
    validColumns = ["price", "quantity", "category", "name"]
    # Get product id 
    pID = input("Enter product ID => ")

    # Print valid columns
    print("Valid columns: ", end="")
    for column in validColumns:
        print(column, end=", ")
    colToChange = input("\nCategory to change => ")
    while colToChange not in validColumns:
        colToChange = input("Invalid category to change => ")

    # What to change
    if colToChange == "price":
        valid = False
        while not valid:
            try:
                changeTo = float(input(f"Change {colToChange} to => "))
                valid = True
            except:
                print("Please enter a float.")
    elif colToChange == "quantity":
        valid = False
        while not valid:
            try:
                changeTo = int(input(f"Change {colToChange} to => "))
                valid = True
            except:
                print("Please enter an integer.")
    else:
        changeTo = input(f"Change {colToChange} to => ")
    
    # Execute change
    cur.execute(f"UPDATE Product SET {colToChange} = (?) WHERE product_id = (?)", (changeTo, pID))
    # Commit 
    con.commit()

def addNewProduct():
    # Get the proper information making sure it follows the correct types
    name = str(input("Enter product name => "))
    category = str(input("Enter product category => "))
    valid = False
    while not valid:
        try:
            price = float(input("Enter product price => "))
            valid = True
        except:
            print("Invalid, please enter a float")
    valid = False
    while not valid:
        try:
            quantity = int(input("Enter product quantity => "))
            valid = True
        except:
            print("Invalid, please enter a int")

    # Insert product 
    cur.execute("INSERT INTO Product (price, quantity, name, category) VALUES (?,?,?,?)", (price, quantity, name, category))

    # Commit
    con.commit()

def updateEmpInfo():
    validColumns = ["first_name", "last_name", "position", "date_hired", "active", "manager"]
    boolToNum = {"true" : 1, 
                 "false" : 0}

    # Get empId
    empId = input("Enter employee ID => ")

    # Print valid columns
    print("Valid columns: ", end="")
    for column in validColumns:
        print(column, end=", ")
    colToChange = input("\n\tCategory to Change => ")
    while colToChange not in validColumns:
        colToChange = input("Invalid category to change => ")
    
    # What to change
    if colToChange == "date_hired":
        changeTo = input(f"Change {colToChange} to (mm/dd/yy)=> ")
        while len(changeTo.split("/")) != 3:
            changeTo = input(f"Invalid Format. Change {colToChange} to (mm/dd/yy)=> ")
    elif colToChange == "active" or colToChange == "manager":
        changeTo = input(f"Change {colToChange} to (true / false) => ")
        valid = False
        while not valid:
            try:
                changeTo = boolToNum[changeTo.lower()]
                valid = True
            except: 
                changeTo = input(f"Change {colToChange} to (true / false) => ")
    else:
        changeTo = input(f"Change {colToChange} to => ")
    
    # Execute query
    cur.execute(f"UPDATE Employee SET {colToChange} = (?) WHERE emp_id = (?)", (changeTo, empId))
    # Commit
    con.commit()

def addEmp():
    # Get info 
    boolToNum = {"y" : 1,
                 "n" : 0}
    firstName = input("First name => ")
    lastName = input("Last name => ")
    position = input("Position => ")
    hireDate = input("Hire date (mm/dd/yyyy) => ")
    while len(hireDate.split("/")) != 3:
        hireDate = input("Invalid. Hire date (mm/dd/yyyy) => ")
    manager = input("Manager status (y / n) => ")
    valid = False
    while not valid:
        try:
            manager = boolToNum[manager.lower()]
            valid = True
        except:
            manager = input("Invalid. Manager status (y / n) => ")
    valid = False
    active = input("Active employee (y / n) => ")
    while not valid:
        try:
            active = boolToNum[active.lower()]
            valid = True
        except:
            active = input("Invalid. Active employee (y / n) => ")
    valid = False
    wage = input("Hourly wage => ")
    while not valid:
        try:
            wage = float(wage)
            valid = True
        except:
            wage = input("Invalid. Hourly wage (no $)=> ")

    
    # Execute the query
    cur.execute("INSERT INTO Employee (first_name, last_name, position, date_hired, active, manager, wage) VALUES (?,?,?,?,?,?,?)", (firstName, lastName, position, hireDate, active, manager, wage))

    # Commit
    con.commit()

def empQuery():
    validColumns = ["first_name", "last_name", "position", "date_hired", "active", "manager", "wage", "*"]
    validNumQueries = ["avg", "min", "max", "median", "std deviation"]
    whereColumn = None

    # Print valid columns to user
    print("Valid Columns: ", end="")
    for column in validColumns:
        print(column, end=", ")

    # Get user selection and validate
    selectedColumn = input("\n\tSelect a column to query => ")
    while selectedColumn not in validColumns:
        selectedColumn = input("Invalid. Select a column to query => ")

    # Check if a numerical column
    if selectedColumn == "wage":
        print("Valid Queries: ", end="")
        for query in validNumQueries:
            print(f"{query}", end=", ")
        selectedQuery = input("\nWrite query => ")
        while selectedQuery not in validNumQueries:
            selectedQuery = input("Invalid query => ")
        
        # Ask to add where
        if input("Add a where restriction? (y / n) => ") == 'y':
            print("Valid Columns: ", end=" ")
            for item in validColumns:
                print(item, end=", ")
            # Get user selection
            whereColumn = input("\nWrite column to restrict => ").lower()
            while whereColumn not in validColumns:
                whereColumn = input("Invalid Column. Write column to restrict => ").lower()
            # Get restriction
            restriction = input(f"Filter where {whereColumn} = ")
        
        # Write the query
        if selectedQuery == "median" or selectedQuery == "std deviation":
            # Just get all info to calculate later
            queryStr = f"SELECT {selectedColumn} FROM Employee"
            if whereColumn != None:
                queryStr += f" WHERE {whereColumn} = {restriction}"
            cur.execute(queryStr)
            returnVal = cur.fetchall()
            # Add values to a list for calculation
            vals = []
            for val in returnVal:
                vals.append(val[0])
            # Print proper output
            if selectedQuery == "median":
                print(f"median wage: {statistics.median(vals)}")
            else:
                print(f"std deviation of wage: {statistics.median(vals)}")
        else:
            # Execute query
            # Just get all info to calculate later
            queryStr = f"SELECT {selectedQuery}({selectedColumn}) FROM Employee"
            if whereColumn != None:
                queryStr += f" WHERE {whereColumn} = {restriction}"
            cur.execute(queryStr)
            returnVal = cur.fetchall()
            print(f"{selectedQuery} {selectedColumn}: {returnVal[0][0]}")
    else:
        # Ask to add where
        if input("Add a where restriction? (y / n) => ") == 'y':
            print("Valid Columns: ", end=" ")
            for item in validColumns:
                print(item, end=", ")
            # Get user selection
            whereColumn = input("\nWrite column to restrict => ").lower()
            while whereColumn not in validColumns:
                whereColumn = input("Invalid Column. Write column to restrict => ").lower()
            # Get restriction
            restriction = input(f"Filter where {whereColumn} = ")
        # Execute query
        queryStr = f"SELECT {selectedColumn} FROM Employee"
        if whereColumn != None:
            if whereColumn == "wage":
                queryStr += f" WHERE {whereColumn} = {restriction}"
            else:
                queryStr += f" WHERE {whereColumn} = '{restriction}'"
        cur.execute(queryStr)
        returnVal = cur.fetchall()
        # Print info
        for row in returnVal:
            for item in row:
                print(f"{item:<15}", end=" ")
            print()

def viewHours():
    # Get name and hours worked
    cur.execute('''SELECT first_name, last_name, hours_in_period, total_hours_worked, active FROM Employee JOIN EmployeeHours ON
                   Employee.emp_id = EmployeeHours.emp_id''')
    returnVal = cur.fetchall()

    # Display
    print("\tHours")
    print("Name                |period_hours|total_hours")
    print("-" * 45)
    for row in returnVal:
        if row[4] == 1:
            print(f"{row[0][:10]:<10} {row[1][:10]:<10} {row[2]:>11.2f} {row[3]:>11.2f}")

def payroll():
    # Get info needed
    cur.execute('''SELECT first_name, last_name, hours_in_period, wage FROM Employee JOIN EmployeeHours ON
                   Employee.emp_id = EmployeeHours.emp_id''')
    returnVal = cur.fetchall()
    # Show the payroll hours
    total = 0
    print("Payroll Hours")
    print("Name               |period hours|total pay")
    print("-" * 45)
    for row in returnVal:
        if row[2] != 0:
            individualPay = row[2] * row[3]
            print(f"{row[0][:10]:<10} {row[1][:10]:<10} {row[2]:>10.2f} {individualPay:>10.2f}")
            total += individualPay
    # Display the total it will cost
    print(f"\n\tTotal payroll: ${total:.2f}")

    # Complete payroll
    completePayroll = input(f"Complete Payroll for ${total:.2f} (y / n) => ")
    while completePayroll.lower() != "y" and completePayroll.lower() != "n":
        completePayroll = input(f"Complete Payroll for ${total:.2f} (y / n) => ")
    if completePayroll.lower() == "y":
        # Set all of the hours in period to 0
        cur.execute("UPDATE EmployeeHours SET hours_in_period = 0")
        con.commit()
        print("Payroll completed") 

def removeFromTable():
    print("WARNING: REMOVING EMPLOYEES OR PRODUCTS CAN LEAD TO INVALID REFERENCES")
    if input("Proceed (y / n) => ") == "y":
        # Get table selection
        validTables = ["Employee", "Orders", "Product"]
        print("Valid tables: ", end ="")
        for table in validTables:
            print(table, end=", ")
        tableSelection = input("\n\tSelect a table => ")
        while tableSelection not in validTables:
            tableSelection = input("Invalid. Select a table => ")

        # Get where
        valid = False
        while not valid:
            try:
                pmkey = int(input("Enter primary key of record to remove: "))
                valid = True
            except:
                print("Invalid. Please enter an integer.")
        
        # Delete from proper tables
        if tableSelection == "Employee":
            # Delete from employee and employee hours
            cur.execute("DELETE FROM Employee WHERE emp_id = (?)", (pmkey,))
            cur.execute("DELETE FROM EmployeeHours WHERE emp_id = (?)", (pmkey,))
        elif tableSelection == "Product":
            # Delete from product
            cur.execute("DELETE FROM Product WHERE product_id = (?)", (pmkey,))
        else:
            # Delete from order and orderproducts
            cur.execute("DELETE FROM Orders WHERE order_id = (?)", (pmkey,))
            cur.execute("DELETE FROM OrderProducts WHERE order_id = (?)", (pmkey,))
        con.commit()
# Call mains
main()