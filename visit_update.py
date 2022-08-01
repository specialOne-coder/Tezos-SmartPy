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
                  visits = sp.big_map(tkey = TAddress, tvalue = sp.record (nb_visit = sp.TNat, interval = sp.TTimestamp))
        )
        
    # get current user
    # verify if user is not already registered
    # add user to users collection 
    # init user interval visit time and visit number
    @sp.entry_point
    def register(self):
        current_user = sp.sender
        sp.verify(~ self.data.visits.contains(current_user), message="Already registered")
        self.data.visits[current_user].nb_visit = 0
        self.data.visits[current_user].interval = sp.now



    # init visit price and get current user
    # init limitTime which will determine the time interval between user visits (1 minute between two visits.)
    # verify if sender is registered and if the amount sent by the user is equal the visit_price
    # Not verify interval time if this is first visit of user
    # update user visitInterval time and user visit number
    @sp.entry_point
    def visit(self):
        visit_price = sp.tez(1)
        current_user = sp.sender
        limitTime = self.data.visits[current_user].interval.add_minutes(1)
        sp.verify(~ self.data.visits.contains(current_user), message="Not registered")
        sp.verify(sp.amount == visit_price,
                  message="The sender did not send the right tez amount (Visit price = 1tz).")
        sp.if self.data.visits[current_user].nb_visit > 0:
            sp.verify(sp.now >= limitTime, message="You made a visit less than a minute ago")
        self.data.visits[current_user].interval = sp.now
        self.data.visits[current_user].nb_visit += 1 
    
    # verify if source is admin of contract
    # send contract tezs to admin
    @sp.entry_point
    def withdraw(self):
        sp.verify_equal(sp.source, self.data.admin, message="You are not admin of this contract.")
        sp.send(sp.source, sp.balance, message = None)
    
    

      

       