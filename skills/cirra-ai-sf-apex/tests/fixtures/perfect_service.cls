public with sharing class AccountService {
    /**
     * @description Applies deterministic transformations in-memory.
     * @param accounts Accounts to process
     * @return Number of records touched
     */
    public static Integer process(List<Account> accounts) {
        if (accounts == null || accounts.isEmpty()) {
            return 0;
        }

        Integer touched = 0;
        for (Account a : accounts) {
            if (a.Name != null) {
                a.Name = a.Name.trim();
                touched++;
            }
        }

        return touched;
    }
}
