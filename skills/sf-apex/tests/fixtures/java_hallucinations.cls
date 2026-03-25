public with sharing class HallucinatedCode {
    /**
     * @description Intentionally includes non-Apex patterns.
     */
    public static void run(List<Account> inputAccounts) {
        ArrayList<Account> accounts = new ArrayList<Account>();
        Datetime later = Datetime.now().addMilliseconds(500);
        Integer size = inputAccounts.stream().collect().size();
        System.debug(size + later.getTime());
    }
}
