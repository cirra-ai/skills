/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */


/**
 * @author Paul Lucas
 * @company       Salesforce
 *
 * @date 1/12/2023
 *
 * TODO:
 */

public without sharing class XDO_Tool_Utilities //NOPMD
{

    public static final Integer DEFAULT_CODE_LENGTH = 6;

    private static List<String> HEX_CHARACTERS = new List<String>{
            '0', '1', '2', '3', '4', '5', '6', '7',
            '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
    };

    /**
     * newCode: Return a random string of numerals, of specified length
     *
     * @param length
     *
     * @return
     */
    public static String getCode(Integer length) {
        return getCode(length, false);
    }

    /**
     * newCode: Return a random string of alphanumeric characters, of specified length
     *
     * @param length
     * @param includeAlpha
     *
     * @return
     */
    public static String getCode(Integer length, Boolean includeAlpha) {
        String code = '';

        // Default the code length
        length = (length == null || length <= 0) ? DEFAULT_CODE_LENGTH : length;

        // Coalesce a random string heap
        while (code.length() <= length) {
            if (includeAlpha) {
                code += EncodingUtil.base64Encode(Crypto.generateAesKey(256)).replaceAll('[/+=]', '');
            } else {
                code += String.valueOf(Math.abs(Crypto.getRandomLong()));
            }
        }

        return code.substring(0, length);
    }
    /**
     * newGuid: Return a guid
     *
     *  How to generate a version 4 GUID (random)
     *
     * 1. Generate 128 random bits
     * 2. Set the version: Take the 7th byte perform an AND operation with 0x0f followed by an OR operation of 0x40.
     * 3. Set the variant: Take the 9th byte perform an AND operation with 0x3f followed by an OR operation of 0x80.
     * 4. Convert the data to hex and add dashes
     *
     * Original: https://salesforce.stackexchange.com/questions/4073/how-to-generate-a-guid-uuid/223381#223381
     *
     * @return
     *
     * Deprecated - Use UUID.randomUUID()
     */
    public static String getGuid() {
        String randomStringAsHex = EncodingUtil.ConvertTohex(Crypto.GenerateAESKey(128));

        String versionHexBits = randomStringAsHex.SubString(14, 16); // 7th bit
        String variantHexBits = randomStringAsHex.SubString(18, 20); // 9th bit

        Integer versionIntBits = convertHexToInt(versionHexBits);
        Integer variantIntBits = convertHexToInt(variantHexBits);

        Integer versionShiftedIntBits = versionIntBits & 15 | 64;  // (i & 0x0f) | 0x40
        Integer variantShiftedIntBits = variantIntBits & 63 | 128; // (i & 0x3f) | 0x80

        String versionShiftedHexBits = convertIntToHex(versionShiftedIntBits); // Always begins with 4
        String variantShiftedHexBits = convertIntToHex(variantShiftedIntBits); // Always begins with one of 8,9,a,b

        String guid = String.format('{0}-{1}-{2}-{3}-{4}', new List<String>{
                randomStringAsHex.SubString(0, 8),
                randomStringAsHex.SubString(8, 12),
                versionShiftedHexBits + randomStringAsHex.SubString(14, 16),
                variantShiftedHexBits + randomStringAsHex.SubString(18, 20),
                randomStringAsHex.substring(20)
        });

        return guid;
    }

    /**
     * convertHexToInt: Return the integer representation for a hexadecimal string
     *
     * @param hex
     *
     * @return
     */
    static Integer convertHexToInt(String hex) {
        Integer d0 = HEX_CHARACTERS.IndexOf(hex.Substring(1, 2));
        Integer d1 = HEX_CHARACTERS.IndexOf(hex.Substring(0, 1));

        return d0 + (d1 * 16);
    }

    /**
     * convertIntToHex: Return the hexadecimal representation for an integer
     *
     * @param intval
     *
     * @return
     */
    static String convertIntToHex(Integer intval) {
        // https://stackoverflow.com/a/13465128
        String hs0 = HEX_CHARACTERS.Get(intval & 15); // i & 0x0f
        String hs1 = HEX_CHARACTERS.Get(((intval >> 4) & 15)); //(i >> 4) & 0x0f

        return hs1 + hs0;
    }


    /**
     * sendMail: Call Messaging.sendEmail
     *
     * @param addresses
     * @param subject
     * @param body
     */
    @Future
    public static void sendMail(String addresses, String subject, String body) {
        List<String> addressList = String.escapeSingleQuotes(addresses)
                .replace(',', ';').
                replace(' ', ';')
                .split(';');

        sendMail(addressList, subject, body);
    }

    /**
     * sendMail: Call Messaging.sendEmail
     *
     * @param addresses
     * @param subject
     * @param body
     */
    public static void sendMail(List<String> addresses, String subject, String body) {
        Messaging.SingleEmailMessage mail = new Messaging.SingleEmailMessage();

        if (addresses != null && !addresses.isEmpty()) {
            Set<String> addressList = new Set<String>(addresses);
            addressList.remove('');
            addressList.remove(null);

            if (!addressList.isEmpty()) {
                mail.setToAddresses(new List<String>(addressList));
                mail.setSubject(subject);
                mail.setPlainTextBody(body);

                try {
                    Messaging.SendEmailResult[] results = Messaging.sendEmail(
                            new Messaging.SingleEmailMessage[]{
                                    mail
                            });
                } catch (EmailException e) {

                }
            }
        }

    }

    /**
     * @param instance
     *
     * @return
     */
    public static String getClassName(Object instance) {
        String className = String.valueOf(instance);

        return className.substringBefore(':');
    }
}