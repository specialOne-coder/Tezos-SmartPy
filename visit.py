# Visit Contract 
# Author: Ferdinand

import smartpy as sp


class Visit(sp.Contract):

    # init contract storage with constructor
    # admin : address of contract admin
    # users : unordered collections of user address
    # visitPerUser : Map that associates each user's address with a visit number.
    # visitInterval : intervals of minutes a user has to wait for each visit 
    def __init__(self, address):
        self.init(admin=address,
                  users=sp.set(),
                  visitPerUser=sp.map(),
                  visitInterval=sp.map()
                  )

    # get current user
    # verify if user is not already registered
    # add user to users collection 
    # init user interval visit time and visit number
    @sp.entry_point
    def register(self):
        current_user = sp.sender
        sp.verify(~ self.data.users.contains(current_user), message="Already registered")
        self.data.users.add(current_user)
        self.data.visitInterval[current_user] = sp.now
        self.data.visitPerUser[current_user] = 0

    # init visit price and get current user
    # init limitTime which will determine the time interval between user visits (1 minute between two visits.)
    # verify if sender is registered and if the amount sent by the user is equal the visit_price
    # Not verify interval time if this is first visit of user
    # update user visitInterval time and user visit number
    @sp.entry_point
    def visit(self):
        visit_price = sp.tez(1)
        current_user = sp.sender
        limitTime = self.data.visitInterval[current_user].add_minutes(1)
        sp.verify(self.data.users.contains(current_user), message="Not registered")
        sp.verify(sp.amount == visit_price,
                  message="The sender did not send the right tez amount (Visit price = 1tz).")
        sp.if self.data.visitPerUser[current_user] > 0:
            sp.verify(sp.now >= limitTime, message="You made a visit less than a minute ago")
        self.data.visitInterval[current_user] = sp.now
        self.data.visitPerUser[current_user] += 1 
    
    # verify if source is admin of contract
    # send contract tezs to admin
    @sp.entry_point
    def withdraw(self):
        sp.verify_equal(sp.source, self.data.admin, message="You are not admin of this contract.")
        sp.send(sp.source, sp.balance, message = None)
    
    
    # test all contract entrypoints
    # test register with different users in different cases
    # test visit with different users in different cases
    # test withdraw with different users
    @sp.add_test(name="Visit")
    def test():
        #init test accounts and test deploy with admin adress
        ferdi = sp.test_account("Ferdi")
        bob = sp.test_account("Bob")
        nomad = sp.test_account("Nomad")
        admin = sp.test_account("Administrator")
        v = Visit(admin.address)
        scenario = sp.test_scenario()
        scenario.h1("Visit")
        scenario += v

        # test register with différent user in different cases
        scenario.h2("Test register entrypoint") 
        scenario.h3("User Ferdi successfully register")  # good registration
        scenario += v.register().run(sender=ferdi.address)
        scenario.verify(v.data.users.contains(ferdi.address))

        scenario.h3("User Bob successfully register") # another user registration
        scenario += v.register().run(sender=bob.address)
        scenario.verify(v.data.users.contains(bob.address))

        scenario.h3("User Ferdi unsuccessfully register") # user already registered
        scenario += v.register().run(sender=ferdi.address, valid=False)

        scenario.h3("User Bob unsuccessfully register") # user already registered
        scenario += v.register().run(sender=bob.address, valid=False)

        # Test visit entrypoint with different user in different cases
        scenario.h2("Test visit entrypoint")        
        scenario.h3("User Ferdi unsuccessfully call visit by sending not enough tez to the contract") # Not enough tez to visit
        scenario += v.visit().run(sender=ferdi.address, valid=False)

        scenario.h3("Not registered user Nomad unsuccessfully call visit") # Not registered user
        scenario += v.visit().run(sender=nomad.address, valid=False)

        scenario.h3("User Ferdi successfully call visit") # good visit
        scenario += v.visit().run(sender=ferdi.address, amount=sp.tez(1), now=sp.timestamp_from_utc_now())
        scenario.verify_equal(v.data.visitPerUser[ferdi.address], 1)
        scenario.verify_equal(v.data.visitInterval[ferdi.address], sp.timestamp_from_utc_now())

        scenario.h3("User Ferdi unsuccessfully call visit because already called it in less than a minute ") # bad visit (less than a minute)
        scenario += v.visit().run(sender=ferdi.address, amount=sp.tez(1), now=sp.timestamp_from_utc_now(), valid=False)
        scenario.verify_equal(v.data.visitPerUser[ferdi.address], 1)


        scenario.h3("User Ferdi successfully call visit after 1 minute") # good visit after 1 minute
        time=sp.timestamp_from_utc_now().add_minutes(1)
        scenario += v.visit().run(sender=ferdi.address, amount=sp.tez(1), now=time)
        scenario.verify_equal(v.data.visitPerUser[ferdi.address], 2)
        scenario.verify_equal(v.data.visitInterval[ferdi.address], time)

        scenario.h3("User Bob successfully call visit") # good visit by another user
        scenario += v.visit().run(sender=bob.address, amount=sp.tez(1), now=sp.timestamp_from_utc_now())
        scenario.verify_equal(v.data.visitPerUser[bob.address], 1)
        scenario.verify_equal(v.data.visitInterval[bob.address], sp.timestamp_from_utc_now())

        scenario.h3("User Bob unsuccessfully call visit because already called it in less than a minute ") # bad visit (less than a minute)
        scenario += v.visit().run(sender=bob.address, amount=sp.tez(1), now=sp.timestamp_from_utc_now(), valid=False)
        scenario.verify_equal(v.data.visitPerUser[bob.address], 1)

        scenario.h3("User Bob successfully call visit after 1 minute") # good visit after 1 minute
        time=sp.timestamp_from_utc_now().add_minutes(1)
        scenario += v.visit().run(sender=bob.address, amount=sp.tez(1), now=time)
        scenario.verify_equal(v.data.visitPerUser[bob.address], 2)
        scenario.verify_equal(v.data.visitInterval[bob.address], time)

        # test withdraw entrypoint with different
        scenario.h2("Test admin withdraw") 
        scenario.h3("User Bob unsuccessfully call withdraw") # Not admin
        scenario += v.withdraw().run(sender=bob.address, valid=False)

        scenario.h3("User nomad unsuccessfully call withdraw") # Not user and not admin test
        scenario += v.withdraw().run(sender=nomad.address, valid=False)
        scenario.show(v.balance)

        scenario.h3("Admin successfully call withdraw") # good withdraw by admin
        scenario += v.withdraw().run(sender=admin.address)
        scenario.show(v.balance)
