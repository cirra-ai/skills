public with sharing class UnsafeMapAccess {
    /**
     * @description Intentionally unsafe map access.
     */
    public static String extractName(Map<Id, Account> byId, Id accountId) {
        return byId.get(accountId).Name;
    }
}
