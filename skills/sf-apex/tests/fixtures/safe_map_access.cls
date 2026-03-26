public with sharing class SafeMapAccess {
    /**
     * @description Safe map access using containsKey checks.
     */
    public static String extractName(Map<Id, Account> byId, Id accountId) {
        if (byId != null && byId.containsKey(accountId)) {
            return byId.get(accountId).Name;
        }
        return null;
    }
}
