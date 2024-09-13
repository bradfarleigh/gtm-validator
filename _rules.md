## Google Tag (gtag.js) Implementation

1. Platform: Use "GA4"
2. Type: "Config"
3. Example: GA4 | Config | Google Tag
4. ID Extraction:
   - Find "tagId" parameter, should match GA4 Measurement ID format

## Custom Template Tags

1. Identify custom templates by checking the "type" field for "cvt_" prefix
2. Apply platform-specific naming conventions even for custom templates
3. Example: FB | Event | Lead (for Facebook custom template)

## Folder Structure

1. Use folders to organize tags by platform or purpose
2. Suggested folder structure:
   - Analytics
   - Advertising
   - Conversion Tracking
   - Utilities
3. Ensure tag names include folder context if not obvious

## Conversion Linker

1. Platform: Use "CLINK"
2. Should be set to fire on all pages
3. Check enableCrossDomain and enableUrlPassthrough settings

## Floodlight (DCM) Tags

1. Platform: Use "DCM" or "FLOODLIGHT"
2. Types: "Global" for configuration, "Event" for specific events
3. Naming convention: DCM | [Event Type] - [Description]
4. Check for consistent advertiser ID across all Floodlight tags
5. Verify groupTag and activityTag follow client's naming convention

## The Trade Desk (TTD) Tags

1. Platform: Use "TTD"
2. Types: "Pixel" for base pixel, "Event" for specific events
3. Naming convention: TTD | [Event Type] - [Description]
4. For HTML implementation, ensure pixel URL is correct and consistent

## Variable Usage

1. Identify all variables used in tags (e.g., {{GA4 - Measurement ID}})
2. Ensure variables are properly defined and contain expected values
3. Use consistent naming convention for variables

## Consent Settings

1. Review consentSettings for each tag
2. Ensure consistent consent configuration across similar tags
3. Verify that consent settings align with the website's privacy policy

## General Tag Auditing

1. Check for duplicate tags with the same functionality
2. Verify that all tags have appropriate firing triggers
3. Ensure tags are placed in the correct folders
4. Check for any tags with NOT_SET consent status and update as necessary

## Tag Consolidation and Consistency

1. Duplicate Functionality:
   - Avoid creating multiple tags that perform the same function.
   - Instead, create a single tag with multiple triggers.
   - Use a generic name that covers all use cases.

   Example:
   Instead of:
     - "FB | Event - Lead - Homepage"
     - "FB | Event - Lead - Contact Page"
   Use:
     - "FB | Event - Lead" (with triggers for both Homepage and Contact Page)

2. Configuration Consistency:
   - For each platform (GA4, Facebook, Floodlight, etc.), ensure all tags use the same configuration ID.
   - Compare IDs across all tags of the same platform and highlight any discrepancies.

3. Naming for Multi-Trigger Tags:
   - Use a naming convention that indicates multiple triggers:
     [Platform] | [Type] - [Event/Action] (Multiple)
   
   Example:
   "GA4 | Event - Page View (Multiple)"

4. Trigger Documentation:
   - For tags with multiple triggers, document all triggers in the tag's notes or description field.

5. Configuration ID Checks:
   - GA4: Ensure all GA4 tags use the same Measurement ID.
   - Facebook: Verify consistent Pixel ID across all FB tags.
   - Floodlight: Check for consistent Advertiser ID.
   - Google Ads: Confirm consistent Conversion ID.

6. Cross-Platform ID Consistency:
   - If a website uses multiple properties (e.g., development, staging, production), ensure proper ID usage for each environment.
   - Consider using lookup tables or environment-specific variables for configuration IDs.

7. Tag Purpose Overlap:
   - Review tags with similar purposes (e.g., pageview tracking) across different platforms.
   - Ensure these tags fire consistently and use the same triggers where appropriate.

8. Custom HTML Tag Consolidation:
   - For custom HTML tags, look for opportunities to combine similar scripts into a single tag with conditional execution based on triggers or custom JavaScript variables.

9. Event Naming Consistency:
   - For tags tracking the same event across platforms (e.g., "Purchase" on GA4, Facebook, and Floodlight), ensure consistent event naming and parameter usage.

10. Variable Usage in Tags:
    - Promote the use of variables for common values (e.g., event names, product IDs) to ensure consistency across tags.
    - Regularly audit variable usage to prevent hard-coded values in tags.

11. Trigger Consolidation:
    - Look for opportunities to create generic triggers that can be used across multiple tags, reducing the need for tag-specific triggers.

12. Regular Tag Audits:
    - Conduct periodic audits to identify and consolidate any tags with overlapping functionality that may have been added over time.

13. Documentation for Consolidated Tags:
    - For tags serving multiple purposes or events, ensure comprehensive documentation within the tag or in a shared document, explaining all use cases and associated triggers.

14. Testing Consolidated Tags:
    - After consolidating tags, perform thorough testing to ensure all previous functionality is maintained across all relevant scenarios and page types.