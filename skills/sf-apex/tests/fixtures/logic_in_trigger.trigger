trigger ContactTrigger on Contact (before insert) {
    for (Contact c : Trigger.new) {
        if (String.isBlank(c.LastName)) {
            c.LastName = 'Unknown';
        }
    }
    List<Account> accounts = [SELECT Id FROM Account];
}
