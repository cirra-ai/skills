public with sharing class BadInlineDmlInLoop {
    /**
     * @description Purposely bad single-line loop body.
     */
    public static void run(List<Account> accounts) {
        for (Account a : accounts) { update a; }
    }
}
