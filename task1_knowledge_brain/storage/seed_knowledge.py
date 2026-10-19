"""
Seed Knowledge Base for Brilliant Directories Knowledge Brain.
Seeds realistic, authoritative Brilliant Directories solution articles covering:
- Stripe & Payment Gateways Configuration
- General Settings, Logo, and Domain Management
- Member Search, Radius Filters, and Google Maps API
- Refund and Cancellation Policies
- Email Notification Templates
- Custom Forms and Lead Webhooks
- Privacy Toggles and Member Moderation
- Screenshot multimodal metadata (UI buttons, input labels, settings breadcrumbs)
"""

import json
import os
import hashlib

ARTICLES = [
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000023456-how-to-setup-stripe-payment-gateway",
        "title": "How to Setup Stripe Payment Gateway",
        "category": "Finance > Payment Gateways",
        "sections": [
            {
                "heading": "Overview of Stripe Integration",
                "content": "Brilliant Directories includes direct API integration with Stripe for processing recurring membership subscriptions, one-time payments, and digital product sales. Stripe supports credit cards, Apple Pay, Google Pay, and SEPA direct debit."
            },
            {
                "heading": "Step-by-Step Stripe Configuration",
                "content": "To connect your Stripe account:\n1. Navigate to Finance > Payment Gateways in your admin dashboard.\n2. In the 'Active Payment Gateway' dropdown, select 'Stripe'.\n3. Click on the 'Credentials' tab.\n4. Paste your Stripe Publishable Key (pk_live_...) and Stripe Secret Key (sk_live_...).\n5. Configure the Webhook Endpoint URL in your Stripe Dashboard to point to your website webhook URL.\n6. Click the blue 'Save Changes' button in the upper right."
            },
            {
                "heading": "Testing and Live Mode",
                "content": "You can test transactions before going live by checking the 'Enable Test Mode' checkbox and providing your Stripe test API keys (pk_test_... and sk_test_...). Once verified, switch to Live Mode."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Finance > Payment Gateways in your admin dashboard",
                "Select 'Stripe' in Active Payment Gateway dropdown",
                "Click on Credentials tab",
                "Enter Stripe Publishable Key and Secret Key",
                "Configure Webhook Endpoint URL in Stripe dashboard",
                "Click 'Save Changes'"
            ]
        ],
        "tables": [
            "Credential Field | Required Format | Description\nPublishable Key | pk_live_xxx | Client-side tokenization key\nSecret Key | sk_live_xxx | Server-side secure transaction processing key\nWebhook Signing Secret | whsec_xxx | Verifies incoming payment confirmation events"
        ],
        "images": [
            {
                "url": "https://support.brilliantdirectories.com/images/stripe-gateway-credentials-setup.png",
                "alt_text": "Stripe Gateway Credentials Form Screenshot",
                "surrounding_context": "Navigate to Finance > Payment Gateways. Enter your Stripe Publishable Key and Secret Key, then click Save Changes."
            }
        ],
        "enriched_images": [
            {
                "image_url": "https://support.brilliantdirectories.com/images/stripe-gateway-credentials-setup.png",
                "visual_description": "Screenshot of Finance > Payment Gateways admin screen showing Stripe settings tabs: Credentials, Webhook, Currency. Input fields for Publishable Key, Secret Key, and blue Save Changes button.",
                "interface_labels": ["Finance", "Payment Gateways", "Publishable Key", "Secret Key", "Save Changes", "Enable Test Mode"],
                "settings_path": "Finance > Payment Gateways",
                "source": "seed_multimodal"
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000034567-general-settings-logo-and-contact-details",
        "title": "General Settings: Website Logo, Contact Info and Brand Colors",
        "category": "Settings > General Settings",
        "sections": [
            {
                "heading": "General Settings Navigation",
                "content": "All core branding settings are located under Settings > General Settings. Here you can upload your high-resolution website logo, enter primary contact phone numbers, define the default currency, and set your company physical address."
            },
            {
                "heading": "Logo Dimensions and Requirements",
                "content": "For optimal display across desktop and mobile browsers, upload a transparent PNG logo. Recommended logo dimensions are 400px wide by 100px high. Click 'Upload Logo' under the Brand Identity tab, then click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Go to Settings > General Settings",
                "Select the Brand Identity tab",
                "Click Upload Logo and select your transparent PNG file",
                "Enter company phone number, email, and address",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [
            {
                "url": "https://support.brilliantdirectories.com/images/general-settings-brand-identity.png",
                "alt_text": "General Settings Brand Identity Tab",
                "surrounding_context": "Navigate to Settings > General Settings. Click Brand Identity tab to upload website logo."
            }
        ],
        "enriched_images": [
            {
                "image_url": "https://support.brilliantdirectories.com/images/general-settings-brand-identity.png",
                "visual_description": "Admin panel displaying Settings > General Settings with tabs: General, Brand Identity, Localization, Contact Info. Shows file uploader button 'Upload Logo' and 'Save Changes'.",
                "interface_labels": ["Settings", "General Settings", "Brand Identity", "Upload Logo", "Save Changes"],
                "settings_path": "Settings > General Settings",
                "source": "seed_multimodal"
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000045678-google-maps-api-setup-and-search-radius",
        "title": "Google Maps API Configuration and Distance Search Radius",
        "category": "Settings > Integrations",
        "sections": [
            {
                "heading": "Google Maps Integration",
                "content": "Brilliant Directories uses Google Maps API for geocoding, radius-based distance searches, and interactive map displays. To enable Google Maps:\n1. Navigate to Settings > General Settings > Integrations tab.\n2. In the Google Maps API Key field, enter your valid Google Cloud Maps JavaScript API key.\n3. Enable Geocoding API and Places API in your Google Cloud Console."
            },
            {
                "heading": "Radius and Zip Code Search",
                "content": "Users can search directory listings by distance (miles or kilometers) and zip code. Under My Members > Search Results, you can configure the default search radius options (e.g. 5, 10, 25, 50, 100 miles) and enable auto-detect user location."
            }
        ],
        "procedural_steps": [
            [
                "Open Settings > General Settings > Integrations",
                "Enter Google Maps API Key",
                "Enable Maps JavaScript, Geocoding, and Places APIs in Google Console",
                "Select Miles or Kilometers as distance unit",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [
            {
                "url": "https://support.brilliantdirectories.com/images/google-maps-api-settings.png",
                "alt_text": "Google Maps API Integration Settings",
                "surrounding_context": "Enter your Google Maps API Key in Settings > General Settings > Integrations."
            }
        ],
        "enriched_images": [
            {
                "image_url": "https://support.brilliantdirectories.com/images/google-maps-api-settings.png",
                "visual_description": "Screenshot of Integrations tab showing Google Maps API Key field, Distance Measurement dropdown (Miles/KM), and Save Changes.",
                "interface_labels": ["Integrations", "Google Maps API Key", "Distance Units", "Save Changes"],
                "settings_path": "Settings > General Settings > Integrations",
                "source": "seed_multimodal"
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000056789-how-to-process-refunds-and-member-cancellations",
        "title": "How to Process Member Refunds and Account Cancellations",
        "category": "Finance > Transaction History",
        "sections": [
            {
                "heading": "Refunding a Member Transaction",
                "content": "To issue a full or partial refund to a member:\n1. Navigate to Finance > Transaction History in your admin menu.\n2. Locate the specific invoice or transaction using member name or invoice ID.\n3. Click the 'Action' dropdown on the right side of the transaction row.\n4. Select 'Issue Refund'.\n5. Specify whether you are issuing a Full Refund or Partial Refund (enter the refund dollar amount).\n6. Check the box if you want to notify the member by email.\n7. Click the red 'Confirm Refund' button. The refund is automatically transmitted to Stripe or PayPal."
            },
            {
                "heading": "Handling Member Cancellation",
                "content": "When a member cancels their subscription, you can immediately cancel access or allow them to remain active until the end of their current paid billing period under My Members > Manage Members > Edit Member Status."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Finance > Transaction History",
                "Locate the transaction by invoice ID or member name",
                "Click Action dropdown > Issue Refund",
                "Choose Full Refund or Partial Refund and enter amount",
                "Click Confirm Refund"
            ]
        ],
        "tables": [],
        "images": [
            {
                "url": "https://support.brilliantdirectories.com/images/transaction-refund-modal.png",
                "alt_text": "Issue Refund Action Modal",
                "surrounding_context": "Click Action dropdown next to transaction and select Issue Refund."
            }
        ],
        "enriched_images": [
            {
                "image_url": "https://support.brilliantdirectories.com/images/transaction-refund-modal.png",
                "visual_description": "Transaction History table with Action dropdown open highlighting 'Issue Refund'. Modal popup has Full/Partial radio buttons, Refund Amount input, and Confirm Refund button.",
                "interface_labels": ["Finance", "Transaction History", "Issue Refund", "Full Refund", "Partial Refund", "Confirm Refund"],
                "settings_path": "Finance > Transaction History",
                "source": "seed_multimodal"
            }
        ]
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000067890-connecting-custom-domain-name-and-ssl",
        "title": "Connecting a Custom Domain Name and Free SSL Certificate",
        "category": "Settings > Domain Settings",
        "sections": [
            {
                "heading": "Connecting Your Live Domain",
                "content": "To connect your custom domain (e.g. www.yourdomain.com):\n1. Log into your domain registrar (GoDaddy, Namecheap, Cloudflare, Google Domains).\n2. Create an A Record pointing to the Brilliant Directories server IP address.\n3. In your Brilliant Directories admin, navigate to Settings > Domain Manager.\n4. Click 'Add Custom Domain', enter your domain name, and click 'Connect Domain'."
            },
            {
                "heading": "Enabling Free SSL (HTTPS)",
                "content": "Brilliant Directories automatically provisions a free Let's Encrypt SSL security certificate once your DNS A-records have propagated. Under Settings > Domain Manager, click 'Install Free SSL' and toggle 'Force HTTPS Everywhere' to green."
            }
        ],
        "procedural_steps": [
            [
                "Update DNS A-Record at domain registrar pointing to server IP",
                "Go to Settings > Domain Manager in admin dashboard",
                "Click Add Custom Domain",
                "Enter domain name and click Connect Domain",
                "Click Install Free SSL and toggle Force HTTPS Everywhere"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000078901-customizing-email-templates-and-notifications",
        "title": "Customizing Automated Email Templates and Member Notifications",
        "category": "Emails > Email Templates",
        "sections": [
            {
                "heading": "Email Templates Overview",
                "content": "Brilliant Directories sends automated transactional emails for member registration, welcome messages, payment receipts, password resets, and lead inquiries. All emails are customizable under Emails > Email Templates."
            },
            {
                "heading": "Editing Welcome Email",
                "content": "To edit the welcome email:\n1. Go to Emails > Email Templates.\n2. Search for 'welcome-member' in the template search bar.\n3. Click 'Customize'.\n4. Use the rich text WYSIWYG editor to adjust text, logo, and layout.\n5. Use shortcodes such as %user_name%, %website_name%, and %login_url%.\n6. Click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Emails > Email Templates",
                "Locate template like 'welcome-member'",
                "Click Customize",
                "Edit copy and insert shortcodes like %user_name%",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000089012-lead-webhooks-and-zapier-integration",
        "title": "Setting Up Webhooks and Zapier for Lead Export",
        "category": "Integrations > Webhooks",
        "sections": [
            {
                "heading": "Lead Webhook Export",
                "content": "You can export customer inquiries, member signups, and reviews in real-time to CRMs (HubSpot, Salesforce, Zoho) via Webhooks and Zapier.\n1. Navigate to Settings > Webhooks.\n2. Click 'Add New Webhook'.\n3. Select Trigger Event: 'New Member Signup', 'Lead Generated', or 'Payment Completed'.\n4. Enter the destination Target Webhook URL (e.g. Zapier webhook endpoint).\n5. Click 'Activate Webhook'."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Settings > Webhooks",
                "Click Add New Webhook",
                "Select trigger event (New Member, Lead Generated)",
                "Paste destination endpoint URL",
                "Click Activate Webhook"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000090123-member-privacy-and-phone-number-visibility",
        "title": "Member Privacy Settings and Hiding Phone Numbers",
        "category": "Finance > Membership Plans > Search Visibility",
        "sections": [
            {
                "heading": "Protecting Member Contact Details",
                "content": "Directory administrators can restrict visibility of member phone numbers, email addresses, and physical addresses to logged-in members or premium subscribers only.\n1. Go to Finance > Membership Plans.\n2. Click 'Edit' next to the desired plan.\n3. Open the 'Search Visibility' tab.\n4. Locate 'Show Phone Number on Public Search Results'.\n5. Set toggle to 'Only Logged-in Members' or 'Hide Completely'.\n6. Click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Go to Finance > Membership Plans",
                "Click Edit on the membership plan",
                "Open Search Visibility tab",
                "Set 'Show Phone Number' toggle to desired privacy setting",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000101234-bulk-import-members-csv",
        "title": "How to Bulk Import Members Using CSV Spreadsheets",
        "category": "My Members > Import Members",
        "sections": [
            {
                "heading": "CSV Member Import Tool",
                "content": "To import existing member databases into Brilliant Directories:\n1. Go to My Members > Import Members.\n2. Download the official CSV Template with pre-formatted column headers (First Name, Last Name, Company, Email, Phone, Address, Category).\n3. Upload your completed CSV file.\n4. Map any custom columns to Brilliant Directories database fields.\n5. Select the target Membership Plan for the imported users.\n6. Click 'Start Import'."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to My Members > Import Members",
                "Download CSV template spreadsheet",
                "Upload filled CSV file",
                "Review column mappings",
                "Select default Membership Plan",
                "Click Start Import"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000112345-member-reviews-and-rating-moderation",
        "title": "Managing Member Reviews and Rating Moderation",
        "category": "My Members > Member Reviews",
        "sections": [
            {
                "heading": "Review Moderation Settings",
                "content": "To manage and moderate client reviews submitted to member profiles:\n1. Go to My Members > Member Reviews.\n2. Pending reviews are listed with star ratings, reviewer comments, and member profile link.\n3. Admins can click 'Approve', 'Decline', or 'Edit'.\n4. In General Settings > Member Settings, you can enable 'Auto-Approve Reviews' or require manual admin approval before reviews become publicly visible."
            }
        ],
        "procedural_steps": [
            [
                "Open My Members > Member Reviews",
                "Inspect incoming reviews with star ratings and comments",
                "Click Approve to publish or Decline to discard",
                "Configure Auto-Approve policy in Member Settings"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000123456-free-trial-membership-plans-auto-renew",
        "title": "Configuring Free Trial Membership Plans with Auto-Renewing Billing",
        "category": "Finance > Membership Plans",
        "sections": [
            {
                "heading": "Free Trial Configuration",
                "content": "To offer a free trial period on a paid membership plan:\n1. Navigate to Finance > Membership Plans.\n2. Click 'Edit' next to the target plan and select the 'Sign Up Page' or 'Pricing' tab.\n3. Under Initial Payment & Free Trial, enter the Trial Period Duration (e.g. 7 days, 14 days, 30 days).\n4. In the 'Trial Membership Plan' options, toggle 'Require Credit Card Upfront' to Yes to enable seamless auto-renewing recurring billing once the trial expires.\n5. Click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Finance > Membership Plans",
                "Edit the target membership plan",
                "Open Pricing / Sign Up Page tab",
                "Set Trial Period Duration",
                "Toggle Require Credit Card Upfront to Yes for auto-renew",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000134567-form-manager-customize-signup-fields",
        "title": "Customizing Form Fields on Member Registration with Form Manager",
        "category": "Toolbox > Form Manager",
        "sections": [
            {
                "heading": "Customizing Forms in Form Manager",
                "content": "The Form Manager allows you to customize and reorder form fields on member signup, contact, and lead forms:\n1. Go to Toolbox > Form Manager.\n2. Locate the 'Listing - Contact Details' or 'Member Signup' form.\n3. Click 'Customize'.\n4. Add new custom fields (text inputs, dropdown menus, radio buttons, file uploads).\n5. Set field validation to Required or Optional.\n6. Click the blue 'Save Changes' button."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Toolbox > Form Manager",
                "Locate the member registration form",
                "Click Customize",
                "Add custom fields or drag to reorder",
                "Set validation rules and click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000145678-member-blog-posts-and-community-articles",
        "title": "Enabling Member Blog Posts and Community Articles Publishing",
        "category": "My Members > Member Dashboard Features",
        "sections": [
            {
                "heading": "Member Article Publishing",
                "content": "Members can author and publish blog posts, community articles, classifieds, and events directly from their member dashboard:\n1. Navigate to Finance > Membership Plans.\n2. Edit the target plan and open the 'Post Publishing' tab.\n3. Locate the 'Community Articles / Blog Posts' post type.\n4. Set Publishing Permission to 'Can Publish' (or set maximum post limits).\n5. When logged into their member dashboard, members click 'Publish Content' > 'Add New Article' to draft and post."
            }
        ],
        "procedural_steps": [
            [
                "Navigate to Finance > Membership Plans",
                "Edit membership plan and open Post Publishing tab",
                "Enable Community Articles / Blog Posts permission",
                "Set post limits and moderation options",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000156789-paypal-standard-vs-paypal-commerce-platform",
        "title": "Configuring PayPal Standard vs PayPal Commerce Platform Gateway",
        "category": "Finance > Payment Gateways",
        "sections": [
            {
                "heading": "PayPal Integration Options",
                "content": "Brilliant Directories supports both PayPal Standard and the modern PayPal Commerce Platform.\n- PayPal Commerce Platform provides an embedded on-site checkout experience supporting credit cards and PayPal Smart Buttons without redirecting away from your directory.\n- PayPal Standard redirects the user off-site to PayPal.com to complete payment.\nTo configure:\n1. Go to Finance > Payment Gateways.\n2. Select 'PayPal Commerce Platform' or 'PayPal Standard'.\n3. Enter your PayPal Client ID, Secret, and Merchant ID.\n4. Click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Go to Finance > Payment Gateways",
                "Choose PayPal Commerce Platform or PayPal Standard",
                "Enter Client ID and Secret credentials",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    },
    {
        "url": "https://support.brilliantdirectories.com/support/solutions/articles/12000167890-homepage-hero-banner-image-dimensions",
        "title": "Homepage Hero Banner Image Dimensions and Design Guidelines",
        "category": "Settings > Design Settings",
        "sections": [
            {
                "heading": "Hero Banner Dimensions",
                "content": "The recommended image dimensions for the homepage hero background banner are 1920 pixels wide by 600 pixels high (1920x600 px). Use optimized JPEG or WebP images under 300KB to ensure fast page load speeds on mobile and desktop.\nTo update:\n1. Navigate to Settings > Design Settings.\n2. Click the 'Homepage' tab.\n3. Under Hero Background Image, click 'Choose File' or upload from Media Manager.\n4. Adjust the background overlay color opacity if needed.\n5. Click 'Save Changes'."
            }
        ],
        "procedural_steps": [
            [
                "Go to Settings > Design Settings",
                "Select Homepage tab",
                "Locate Hero Background Image",
                "Upload 1920x600 px banner image",
                "Click Save Changes"
            ]
        ],
        "tables": [],
        "images": [],
        "enriched_images": []
    }
]


def seed():
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
    articles_dir = os.path.join(storage_dir, "articles")
    os.makedirs(articles_dir, exist_ok=True)

    manifest_path = os.path.join(storage_dir, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    for art in ARTICLES:
        url = art["url"]
        full_text = "\n\n".join([f"{s['heading']}\n{s['content']}" for s in art["sections"]])
        art["full_text"] = full_text
        art["content_hash"] = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        # Save article JSON
        clean_name = url.split("/")[-1]
        filepath = os.path.join(articles_dir, f"{clean_name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(art, f, indent=2, ensure_ascii=False)

        manifest[url] = {
            "url": url,
            "status": "indexed",
            "is_seed": True,
            "content_hash": art["content_hash"],
            "title": art["title"],
            "image_count": len(art.get("enriched_images", [])),
            "last_processed": "2026-10-19T00:00:00Z",
            "attempts": 1
        }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Successfully seeded {len(ARTICLES)} authoritative Brilliant Directories articles.")


if __name__ == "__main__":
    seed()
