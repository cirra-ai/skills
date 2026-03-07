trigger AccountTrigger on Account (before insert) {
    for (Account a : Trigger.new) {
        if (String.isBlank(a.Name)) {
            a.Name = 'New Account';
        }
    }
}
