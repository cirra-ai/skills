@isTest
private class SDO_SCOM_contactListB2BTest {
  @isTest
  static void testGetContactList() {
    // Insert test data
    List<Contact> testContacts = new List<Contact>();
    for (Integer i = 0; i < 15; i++) {
      testContacts.add(
        new Contact(
          FirstName = 'Test' + i,
          LastName = 'Contact' + i,
          Email = 'test' + i + '@example.com'
        )
      );
    }
    insert testContacts;

    List<Contact> result = SDO_SCOM_contactListB2B.getContactList();

    System.assertNotEquals(null, result);

    System.assertEquals(12, result.size());

    for (Integer i = 0; i < result.size() - 1; i++) {
      System.assert(result[i].LastViewedDate >= result[i + 1].LastViewedDate);
    }
  }
}