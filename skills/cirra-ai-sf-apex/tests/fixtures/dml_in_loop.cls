public with sharing class BadDmlInLoop {
    /**
     * @description Purposely bad pattern used as validator fixture.
     */
    public static void run(List<Account> accounts) {
        for (Account a : accounts) {
            update a;
        }
    }
}
