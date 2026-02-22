/**
 * @description Service class for Account operations.
 *              Provides methods for querying, creating, and updating Accounts.
 * @author      CirraTest
 * @date        2025-01-15
 */
public with sharing class CirraTest_AccountService {

    /**
     * @description Get accounts by IDs with related contacts.
     * @param accountIds Set of Account IDs to query.
     * @return List of Account records with Contacts.
     */
    public static List<Account> getAccountsWithContacts(Set<Id> accountIds) {
        if (accountIds == null || accountIds.isEmpty()) {
            return new List<Account>();
        }
        return [
            SELECT Id, Name, Industry, AnnualRevenue, BillingCity,
                   (SELECT Id, FirstName, LastName, Email, Title FROM Contacts)
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
    }

    /**
     * @description Create accounts with validation.
     * @param accounts List of Account records to insert.
     * @return List of Database.SaveResult.
     */
    public static List<Database.SaveResult> createAccounts(List<Account> accounts) {
        if (accounts == null || accounts.isEmpty()) {
            throw new AccountServiceException('Account list cannot be null or empty.');
        }
        for (Account acc : accounts) {
            if (String.isBlank(acc.Name)) {
                throw new AccountServiceException('Account Name is required.');
            }
        }
        return Database.insert(accounts, AccessLevel.USER_MODE);
    }

    /**
     * @description Update account annual revenue in bulk.
     * @param revenueByAccountId Map of Account ID to new AnnualRevenue.
     * @return List of Database.SaveResult.
     */
    public static List<Database.SaveResult> updateAnnualRevenue(Map<Id, Decimal> revenueByAccountId) {
        if (revenueByAccountId == null || revenueByAccountId.isEmpty()) {
            return new List<Database.SaveResult>();
        }
        List<Account> accountsToUpdate = new List<Account>();
        for (Id accountId : revenueByAccountId.keySet()) {
            accountsToUpdate.add(new Account(
                Id = accountId,
                AnnualRevenue = revenueByAccountId.get(accountId)
            ));
        }
        return Database.update(accountsToUpdate, AccessLevel.USER_MODE);
    }

    /**
     * @description Transfer account ownership.
     * @param accountIds Set of Account IDs to transfer.
     * @param newOwnerId New owner User ID.
     * @return List of Database.SaveResult.
     */
    public static List<Database.SaveResult> transferOwnership(Set<Id> accountIds, Id newOwnerId) {
        if (accountIds == null || accountIds.isEmpty()) {
            throw new AccountServiceException('Account IDs cannot be null or empty.');
        }
        if (newOwnerId == null) {
            throw new AccountServiceException('New owner ID cannot be null.');
        }
        List<Account> accountsToUpdate = new List<Account>();
        for (Id accountId : accountIds) {
            accountsToUpdate.add(new Account(
                Id = accountId,
                OwnerId = newOwnerId
            ));
        }
        return Database.update(accountsToUpdate, AccessLevel.USER_MODE);
    }

    public class AccountServiceException extends Exception {}
}
