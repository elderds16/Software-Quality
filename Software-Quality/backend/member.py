from backend.log import Log
from backend.response import CustomResponse
from site_packages.database import Database
from datetime import datetime
import random

from site_packages.encryption import RSA


def get_member(event):
    """
    Get a member by their ID from the database
    :param event: which is the event dict structured as follows:
    :return: the member dict with status code and message
    """
    # check for body in event
    if not event.get("body"):
        return {"statusCode": 400, "Message": "No body provided"}
    if not event.get("memberId"):
        return {"statusCode": 400, "Message": "No member given"}
    member_id = event["memberId"]

    with Database() as (_, cur):
        try:
            cur.execute(
                """
                SELECT *
                FROM member 
                WHERE id = :member_id
                """,
                {"member_id": member_id},
            )
        except Exception as e:
            return {"statusCode": 400, "message": "Could not fetch member: " + str(e)}

        member = cur.fetchone()

    return {"statusCode": 200, "message": "Ok", "member": member}


def get_members(event):
    """
    Get all members from the database and filter them based on the search query
    :param event: which is the event dict structured as follows:
    {
        header: {
            searchQuery: which is the search query to filter the members
        }
    }
    :return: the members dict with status code and message
    """
    # this function is refactored since the data is encrypted now. so we cannot search the data directly
    # we need to decrypt the data first and then search it
    search_query = event.get("header", {}).get("searchQuery", "")
    with Database() as (_, cur):
        try:
            cur.execute(
                """
                SELECT *
                FROM member 
                """,
            )
        except Exception as e:
            return CustomResponse(400, event.get("body", {}).get("invokerUsername"), "Could not fetch members", str(e), False)

        fetch = cur.fetchall()

        decrypted_members = []
        for member in fetch:
            decrypted_members.append(
                {
                    "id": member[0],
                    "first_name": RSA().decrypt(member[1]),
                    "last_name": RSA().decrypt(member[2]),
                    "age": RSA().decrypt(member[3]),
                    "gender": RSA().decrypt(member[4]),
                    "weight": RSA().decrypt(member[5]),
                    "address": RSA().decrypt(member[6]),
                    "email_address": RSA().decrypt(member[7]),
                    "mobile_phone": RSA().decrypt(member[8]),
                    "created_on": member[9]
                }
            )

    # filter the data based on search query
    filtered_members = []
    for member in decrypted_members:
        if search_query in str(member["id"]) or search_query in str(member["first_name"]) or search_query in str(member["last_name"]) or search_query in str(member["address"]) or search_query in str(member["email_address"]) or search_query in str(member["mobile_phone"]):
            filtered_members.append(member)

    Log().log_activity(event.get("body", {}).get("invokerUsername"), "Successfully retrieved members", 'Filtered on: ' + search_query if search_query else 'Retrieved all members', False)
    return {"statusCode": 200, "message": "Successfully retrieved members", "members": filtered_members}


def generate_membership_id():
    """
    Generate a random membership ID for a new member
    :return: the membership ID
    """
    # Get the last two digits of the current year
    current_year = datetime.now().year % 100  # E.g., 2024 -> 24
    first_two_digits = [current_year // 10, current_year % 10]

    # Generate seven random digits
    random_digits = [random.randint(0, 9) for _ in range(7)]

    # Combine the first two digits and random digits
    first_nine_digits = first_two_digits + random_digits
    
    # Calculate checksum
    checksum = sum(first_nine_digits) % 10
    
    # Construct the final ID
    membership_id = ''.join(map(str, first_nine_digits)) + str(checksum)
    
    return membership_id


def add_member(event):
    """
    Add a new member to the database
    :param event: which is the event dict structured as follows:
    {
        body: {
            invokerUsername: which is the username of the user who invoked the function
            firstName: which is the first name of the member
            lastName: which is the last name of the member
            age: which is the age of the member
        }
    }
    :return: the status code and message
    """
    invokerUsername = event.get("body", {}).get("invokerUsername")

    if not event.get("body"):
        return CustomResponse(400, invokerUsername, "No body provided", "tried to add member without a body", False)
    
    body = event["body"]

    if not body.get("firstName"):
        return CustomResponse(400, invokerUsername, "No first name provided", "tried to add member without a first name", False)

    # Generate membership ID
    membership_id = generate_membership_id()  # Ensure this function is defined elsewhere

    # Extract the data from the body
    first_name = body["firstName"]
    last_name = body.get("lastName")
    age = body.get("age")
    age = str(age) if age else None
    gender = body.get("gender")
    weight = body.get("weight")
    weight = str(weight) if weight else None
    address = body.get("address")
    email_address = body.get("emailAddress")
    mobile_phone = body.get("mobilePhone")  # Use the formatted mobile number from UI
    created_on = datetime.now().replace(microsecond=0)

    # encrypt all the data
    encrypted_first_name = RSA().encrypt(first_name)
    encrypted_last_name = RSA().encrypt(last_name)
    encrypted_address = RSA().encrypt(address)
    encrypted_email_address = RSA().encrypt(email_address)
    encrypted_mobile_phone = RSA().encrypt(mobile_phone)
    encrypted_age = RSA().encrypt(age)
    encrypted_weight = RSA().encrypt(weight)
    encrypted_gender = RSA().encrypt(gender)


    with Database() as (_, cur):
        try:
            cur.execute(
                """
                INSERT INTO member 
                    (id, first_name, last_name, age, gender, weight, address, email_address, mobile_phone, created_on)
                VALUES 
                    (:membership_id, :first_name, :last_name, :age, :gender, :weight, :address, :email_address, :mobile_phone, :created_on)
                """, {
                    "membership_id": membership_id,
                    "first_name": encrypted_first_name,
                    "last_name": encrypted_last_name,
                    "age": encrypted_age,
                    "gender": encrypted_gender,
                    "weight": encrypted_weight,
                    "address": encrypted_address,
                    "email_address": encrypted_email_address,
                    "mobile_phone": encrypted_mobile_phone,
                    "created_on": created_on
                }
            )
        except Exception as e:
            return CustomResponse(500, invokerUsername, "Could not add member", str(e), False)

    Log().log_activity(invokerUsername, "Successfully added member", f"ID: {membership_id} | name: {first_name} {last_name}", False)
    return {"statusCode": 200, "message": "Member added successfully.", "membershipId": membership_id}


def modify_member(event):
    """
    Modify an existing member in the database based on the provided data
    :param event: which is the event dict structured as follows:
    {
        body: {
            memberId: which is the ID of the member to modify
            invokerUsername: which is the username of the user who invoked the function
            firstName: which is the first name of the member
            lastName: which is the last name of the member
            age: which is the age of the member
        }
    }
    :return: the status code and message
    """
    if not event.get("body") or not event["body"].get("memberId"):
        return {"statusCode": 400, "Message": "No member ID or body provided."}
    member_id = event["body"]["memberId"]
    updates = {}

    # Prepare the updates
    if event["body"].get("firstName"):
        updates["first_name"] = RSA().encrypt(event["body"]["firstName"])
    if event["body"].get("lastName"):
        updates["last_name"] = RSA().encrypt(event["body"]["lastName"])
    if event["body"].get("age"):
        updates["age"] = RSA().encrypt(str(event["body"]["age"]))
    if event["body"].get("gender"):
        updates["gender"] = RSA().encrypt(event["body"]["gender"])
    if event["body"].get("weight"):
        updates["weight"] = RSA().encrypt(str(event["body"]["weight"]))
    if event["body"].get("address"):
        updates["address"] = RSA().encrypt(event["body"]["address"])
    if event["body"].get("emailAddress"):
        updates["email_address"] = RSA().encrypt(event["body"]["emailAddress"])
    if event["body"].get("mobilePhone"):
        updates["mobile_phone"] = RSA().encrypt(event["body"]["mobilePhone"])

    if not updates:
        return {"statusCode": 400, "message": "No updates provided."}

    # Create the SET clause for the SQL query
    set_clause = ", ".join(f"{key} = :{key}" for key in updates.keys())

    with Database() as (_, cur):
        try:
            cur.execute(
                f"""
                UPDATE member
                SET {set_clause}
                WHERE id = :member_id
                """,
                {**updates, "member_id": member_id}
            )
            if cur.rowcount == 0:
                return CustomResponse(404, event.get("body", {}).get("invokerUsername"), "Member not found", f"Member ID: {member_id}", False)
        except Exception as e:
            print(e)
            return CustomResponse(500, event.get("body", {}).get("invokerUsername"), "Could not update member", str(e), False)

    return CustomResponse(200, event.get("body", {}).get("invokerUsername"), "Successfully updated member", f"Member ID: {member_id}", False)


def delete_member(event):
    """
    Delete a member from the database based on the provided member ID
    :param event: which is the event dict structured as follows:
    {
        body: {
            memberId: which is the ID of the member to delete
            invokerUsername: which is the username of the user who invoked the function
        }
    }
    :return: the status code and message
    """
    if not event.get("body"):
        return {"statusCode": 400, "Message": "No body provided."}
    body = event["body"]

    if not body.get("memberId"):
        return {"statusCode": 400, "Message": "No member ID provided."}
    member_id = body["memberId"]

    with Database() as (_, cur):
        try:
            cur.execute(
                """
                DELETE FROM member
                WHERE id = :member_id
                """,
                {"member_id": member_id},
            )
            if cur.rowcount == 0:
                return CustomResponse(404, body.get("invokerUsername"), "Member not found", f"Member ID: {member_id}", False)
        except Exception as e:
            print(e)
            return CustomResponse(500, body.get("invokerUsername"), "Could not delete member", str(e), False)

    return CustomResponse(200, body.get("invokerUsername"), "Successfully deleted member", f"Member ID: {member_id}", False)
