// export interface CampaignPost {
  id: string;
  date: string;
  day: string;
  platform: string[];
  pillar: string;
  contentType: string;
  title: string;
  content: string;
  imageUrl?: string;
  imagePrompt: string;
  expectedOutcome: string;
  cta: string;
  week: number;
  phone?: string;
  website?: string;
}

// export interface WeekData {
  week: number;
  startDate: string;
  endDate: string;
  theme: string;
  goal: string;
  posts: CampaignPost[];
}

// export interface PillarStats {
  name: string;
  color: string;
  posts: number;
  description: string;
  keyMessage: string;
}

// export interface PlatformStats {
  name: string;
  icon: string;
  color: string;
  users: string;
  bestTimes: string;
  posts: number;
}

const ETHIOBIZ_PHONE = "+251-986-76-7576";
const ETHIOBIZ_WEBSITE = "https://ethiobiz.et";
const ETHIOBIZ_EMAIL = "biz.technology@outlook.com";

const = {
  tibeb: {
    name: "Tibeb (Soul)",
    color: "from-amber-600 to-amber-500",
    posts: 8,
    description: "Worship of the Soul - Preserving Ethiopia's spiritual heritage and cultural wisdom",
    keyMessage: "Discover the light within our shared history",
  },
  dagu: {
    name: "Dagu (Mind)",
    color: "from-blue-600 to-blue-500",
    posts: 7,
    description: "Knowledge of the Mind - The Internet of Truth with verified wisdom and practical learning",
    keyMessage: "What have your eyes seen? Learn the truth",
  },
  magala: {
    name: "Magala (Body)",
    color: "from-emerald-600 to-emerald-500",
    posts: 9,
    description: "Marketplace of the Body - Work as worship, prosperity through integrity with DOBiz Smart ERP",
    keyMessage: "Build your business on a foundation of trust",
  },
  walta: {
    name: "Walta (Support & Security)",
    color: "from-purple-600 to-purple-500",
    posts: 3,
    description: "Support System - 24/7 helpdesk, account security, and user protection across all EthioBiz pillars",
    keyMessage: "Your trusted guardian across all pillars",
  },
  afocha: {
    name: "Afocha (Heart)",
    color: "from-rose-600 to-rose-500",
    posts: 7,
    description: "Love of the Heart - Community connection and collective growth",
    keyMessage: "Together we thrive, as we always have",
  },
  general: {
    name: "General EthioBiz",
    color: "from-slate-600 to-slate-500",
    posts: 11,
    description: "Overall vision and ecosystem messaging - One Civilization. Many Paths",
    keyMessage: "One Civilization. Many Paths",
  },
};

const = {
  telegram: {
    name: "Telegram",
    icon: "✈️",
    color: "bg-blue-500",
    users: "10M+",
    bestTimes: "8:00 AM, 2:00 PM (EAT)",
    posts: 14,
  },
  facebook: {
    name: "Facebook",
    icon: "f",
    color: "bg-blue-600",
    users: "12M+",
    bestTimes: "8:00 AM, 2:00 PM, 6:00 PM (EAT)",
    posts: 14,
  },
  instagram: {
    name: "Instagram",
    icon: "📷",
    color: "bg-pink-500",
    users: "3M+",
    bestTimes: "9:00 AM, 3:00 PM (EAT)",
    posts: 14,
  },
};

const campaignWeeks = [
  {
    week: 1,
    startDate: "2026-04-04",
    endDate: "2026-04-10",
    theme: "The Unseen Thread & Vision Launch",
    goal: "Establish foundational vision with Tibeb focus, introduce the five pillars, and build anticipation",
    posts: [
      {
        id: "w1p1",
        date: "2026-04-04",
        day: "Saturday",
        platform: ["telegram", "facebook"],
        pillar: "general",
        contentType: "Vision Statement",
        title: "One Civilization. Many Paths.",
        content: `🌍 EthioBiz is here to harmonize Ethiopia's rich heritage with modern innovation.

Discover a digital ecosystem built on five pillars:
🕌 Tibeb (Soul) - Worship and spiritual connection
🧠 Dagu (Mind) - Knowledge and verified wisdom
💼 Magala (Body) - Marketplace and prosperity
🛡️ Walta (Self) - Security and protection
❤️ Afocha (Heart) - Community and love

By The Will of God, we are building a better future for Ethiopia, Africa, and humanity.

#EthioBiz #OneEthiopia #DigitalEcosystem #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p1_vision_launch_5d118004.png",
        imagePrompt: "EthioBiz Vision Launch - Ethiopian landscape with five symbolic pillars representing Tibeb, Dagu, Magala, Walta, Afocha",
        expectedOutcome: "Establish brand awareness, introduce vision, 50K+ impressions",
        cta: `🔗 Learn More: ${ETHIOBIZ_WEBSITE}
📞 Call: ${ETHIOBIZ_PHONE}
💬 Telegram: @EthioBiz_Official`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p2",
        date: "2026-04-05",
        day: "Sunday",
        platform: ["telegram", "instagram"],
        pillar: "tibeb",
        contentType: "Pillar Introduction",
        title: "Tibeb: Worship of the Soul",
        content: `🕌 TIBEB - Worship of the Soul

Ethiopia's spiritual heritage runs deep. From ancient times to today, our souls have been nourished by faith, tradition, and connection to something greater.

Tibeb is about:
✨ Honoring our heritage
🙏 Spiritual connection
💫 Inner peace and purpose
🌟 Community worship

Coming soon: Tibeb features on EthioBiz
#Tibeb #Soul #Heritage #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p2_tibeb_teaser_07c7a211.png",
        imagePrompt: "Tibeb pillar - Sacred Ethiopian spiritual imagery with golden light, ancient churches, and spiritual symbols",
        expectedOutcome: "Introduce Tibeb pillar, 40K+ impressions, 2K+ engagements",
        cta: `📖 Learn about Tibeb: ${ETHIOBIZ_WEBSITE}/tibeb
📞 ${ETHIOBIZ_PHONE}
🔔 Subscribe: @Tibeb_Soul`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p3",
        date: "2026-04-06",
        day: "Monday",
        platform: ["facebook", "instagram"],
        pillar: "tibeb",
        contentType: "Video Teaser",
        title: "Tibeb Video Teaser - Coming Soon",
        content: `🎬 Tibeb Video Teaser

Experience the soul of Ethiopia. A journey through our spiritual heritage, traditions, and the timeless wisdom that guides us.

Watch the full Tibeb story launching this week on EthioBiz.

#Tibeb #EthioBiz #Ethiopian #Heritage #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p3_tibeb_video_7b82bc89.png",
        imagePrompt: "Tibeb video teaser - Cinematic Ethiopian landscape with spiritual elements, traditional music, and cultural imagery",
        expectedOutcome: "Build anticipation for Tibeb launch, 45K+ impressions",
        cta: `🎥 Watch Full Video: ${ETHIOBIZ_WEBSITE}/tibeb
📞 Contact: ${ETHIOBIZ_PHONE}
💬 Join: @EthioBiz_Official`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p4",
        date: "2026-04-07",
        day: "Tuesday",
        platform: ["telegram", "facebook"],
        pillar: "dagu",
        contentType: "Pillar Introduction",
        title: "Dagu: Knowledge of the Mind",
        content: `🧠 DAGU - Knowledge of the Mind

"What have your eyes seen? What have your ears heard?"

For centuries, Dagu has been the unbroken chain of verified wisdom. Today, it evolves into your trusted path for knowledge and growth.

Dagu is about:
👁️ Seen & Heard - Information validated by direct witness
🤝 Shared Responsibility - Every individual is a guardian of knowledge
⚖️ Verified Wisdom - Truth filters to the top

Coming soon: Dagu Learning Center with verified courses and expert instructors.

#Dagu #Knowledge #Wisdom #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p4_dagu_teaser_5f717f99.png",
        imagePrompt: "Dagu pillar - Indigo blue learning center imagery with ancient scrolls, knowledge symbols, and modern learning elements",
        expectedOutcome: "Introduce Dagu pillar, 42K+ impressions, 2.2K+ engagements",
        cta: `📚 Learn about Dagu: ${ETHIOBIZ_WEBSITE}/dagu
📞 ${ETHIOBIZ_PHONE}
🔔 Subscribe: @Dagu_Mind`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p5",
        date: "2026-04-08",
        day: "Wednesday",
        platform: ["instagram", "facebook"],
        pillar: "magala",
        contentType: "Pillar Introduction",
        title: "Magala: Marketplace of the Body",
        content: `💼 MAGALA - Marketplace of the Body

Work as Worship. Prosperity as a Fruit of Integrity.

Magala is the realm where we engage our bodies in the world—our work, our health, our material success. This pillar teaches that honest labor is a form of worship.

Magala features:
✅ DOBiz Smart ERP - Cloud business management for all industries
💼 Jobs Portal - Find and hire top talent
🛍️ Shop Marketplace - Reach global markets
🤖 Hadeeda BizAI - Your 24/7 business assistant

Join 10+ active businesses already thriving on Magala.

#Magala #Business #Entrepreneurship #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p5_magala_teaser_4e952ccb.png",
        imagePrompt: "Magala pillar - Earth green marketplace imagery with Ethiopian businesses, shops, and prosperity symbols",
        expectedOutcome: "Introduce Magala pillar, 48K+ impressions, 2.5K+ engagements",
        cta: `💼 Explore Magala: ${ETHIOBIZ_WEBSITE}/magala
📞 ${ETHIOBIZ_PHONE}
🚀 Start Free Trial: [REGISTER_LINK]`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p6",
        date: "2026-04-08",
        day: "Tuesday",
        platform: ["telegram", "facebook"],
        pillar: "walta",
        contentType: "Feature Introduction",
        title: "Walta: Your Support Guardian",
        content: `🛡️ WALTA - Your Support & Security Guardian

Everyone needs a trusted guardian. That's Walta.

Walta is EthioBiz's dedicated support and security system, protecting you across all pillars. Whether you're learning with Dagu, building with Magala, or connecting with Tibeb and Afocha—Walta is there to support you.

Walta provides:
🔐 24/7 Helpdesk Support - Instant assistance whenever you need it
🛡️ Account Security - Two-factor authentication and privacy protection
💻 Secure Transactions - Protected business operations
🔒 Account Recovery - Fast and secure account restoration

Your trusted guardian across all EthioBiz pillars.

#Walta #Support #Security #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p6_walta_teaser_d2bff53e.png",
        imagePrompt: "Walta Support System - Purple guardian protecting users across multiple pillars, helpdesk imagery, security shields, 24/7 support concept",
        expectedOutcome: "Introduce Walta support system, 35K+ impressions, 1.6K+ engagements",
        cta: `🛡️ Access Walta Support: ${ETHIOBIZ_WEBSITE}/walta
📞 24/7 Support: ${ETHIOBIZ_PHONE}
💬 Telegram Support: [TELEGRAM_SUPPORT_LINK]
🔔 Subscribe: @EthioBiz_Support`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w1p7",
        date: "2026-04-10",
        day: "Friday",
        platform: ["facebook", "instagram"],
        pillar: "afocha",
        contentType: "Pillar Introduction",
        title: "Afocha: Love of the Heart",
        content: `❤️ AFOCHA - Love of the Heart

Community is our strength. Connection is our power.

Afocha is about the bonds that hold us together—family, friendship, community, and collective purpose. In the digital age, Afocha reminds us that technology serves humanity, not the other way around.

Afocha features:
💝 Community Connection - Build meaningful relationships
🤝 Collective Support - Help each other thrive
❤️ Shared Values - United by purpose
🌍 Global Community - One humanity

Coming soon: Afocha community features and connection tools.

#Afocha #Community #Love #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w1p7_afocha_teaser_1d816519.png",
        imagePrompt: "Afocha pillar - Red heart imagery with community connections, Ethiopian people, and unity symbols",
        expectedOutcome: "Introduce Afocha pillar, 44K+ impressions, 2.3K+ engagements",
        cta: `❤️ Join Afocha: ${ETHIOBIZ_WEBSITE}/afocha
📞 ${ETHIOBIZ_PHONE}
🔔 Subscribe: @Afocha_Community`,
        week: 1,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
    ],
  },
  {
    week: 2,
    startDate: "2026-04-11",
    endDate: "2026-04-17",
    theme: "Wisdom, Growth & Security",
    goal: "Deepen engagement with Tibeb, Dagu, and Walta; introduce DOBiz Smart ERP; build community",
    posts: [
      {
        id: "w2p1",
        date: "2026-04-11",
        day: "Saturday",
        platform: ["telegram", "facebook"],
        pillar: "tibeb",
        contentType: "Full Feature",
        title: "Tibeb Full Launch - Worship of the Soul",
        content: `🕌 TIBEB IS NOW LIVE

Experience the soul of Ethiopia through Tibeb—a platform dedicated to preserving our spiritual heritage and connecting us to timeless wisdom.

Tibeb Features:
📖 Sacred Stories - Ethiopia's spiritual history
🎵 Traditional Music - Authentic Ethiopian melodies
🙏 Community Worship - Connect with believers
💫 Spiritual Guidance - Wisdom for daily life
🌟 Heritage Preservation - Keep our traditions alive

Join thousands discovering the light within our shared history.

#Tibeb #Soul #Heritage #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p1_tibeb_full_video_cd94f0ea.png",
        imagePrompt: "Tibeb full launch - Beautiful Ethiopian spiritual imagery with ancient churches, sacred sites, and spiritual energy",
        expectedOutcome: "Tibeb full launch, 60K+ impressions, 3K+ engagements, 500+ signups",
        cta: `🕌 Experience Tibeb: ${ETHIOBIZ_WEBSITE}/tibeb
📞 ${ETHIOBIZ_PHONE}
💬 Join: @Tibeb_Soul`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p2",
        date: "2026-04-12",
        day: "Sunday",
        platform: ["instagram", "facebook"],
        pillar: "tibeb",
        contentType: "Blog Post",
        title: "Blog: The Spiritual Roots of Ethiopian Innovation",
        content: `📖 NEW BLOG POST

"The Spiritual Roots of Ethiopian Innovation"

Explore how Ethiopia's ancient wisdom traditions inform modern innovation. From the spiritual practices of our ancestors to the digital tools of today, discover how Tibeb bridges tradition and technology.

Read the full article on our blog and learn:
✨ How spiritual values guide innovation
🌟 The role of faith in Ethiopian entrepreneurship
💫 Building technology with purpose and integrity

#Tibeb #Innovation #Heritage #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p2_tibeb_blog_ea3496a5.png",
        imagePrompt: "Tibeb blog - Artistic blend of ancient Ethiopian spiritual symbols with modern technology elements",
        expectedOutcome: "Blog engagement, 35K+ impressions, 1.5K+ clicks",
        cta: `📖 Read Full Blog: ${ETHIOBIZ_WEBSITE}/blog/spiritual-roots
📞 ${ETHIOBIZ_PHONE}
💬 Share your thoughts: @EthioBiz_Official`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p3",
        date: "2026-04-13",
        day: "Monday",
        platform: ["telegram", "facebook"],
        pillar: "dagu",
        contentType: "Interactive Poll",
        title: "Dagu Poll: What Knowledge Do You Want to Learn?",
        content: `🧠 DAGU POLL - Your Voice Matters

What skills would you like to master on Dagu Learning Center?

Vote now:
📊 A) DOBiz Smart ERP System
📊 B) Digital Marketing Mastery
📊 C) Managerial Accounting
📊 D) All of the above!

Your vote helps us prioritize courses that matter most to you.

Cast your vote in our Telegram channel: @Dagu_Mind

#Dagu #Learning #Community #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p3_dagu_poll_8bb87a39.png",
        imagePrompt: "Dagu poll - Indigo blue interactive poll design with learning symbols and engagement elements",
        expectedOutcome: "Community engagement, 40K+ impressions, 3K+ votes",
        cta: `🗳️ Vote Now: @Dagu_Mind
📞 ${ETHIOBIZ_PHONE}
📚 Learn More: ${ETHIOBIZ_WEBSITE}/dagu`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p4",
        date: "2026-04-14",
        day: "Tuesday",
        platform: ["instagram", "facebook"],
        pillar: "magala",
        contentType: "Feature Highlight",
        title: "Magala Spotlight: SME Success Stories",
        content: `💼 MAGALA SPOTLIGHT - SME Success Stories

Meet the entrepreneurs building Ethiopia's future with DOBiz Smart ERP.

From retail shops to service providers, from educators to manufacturers—DOBiz is empowering small and medium enterprises across all sectors.

Success Stories:
✅ Addis Retail Co. - 300% inventory efficiency
✅ Tech Services Ltd. - 50+ jobs created
✅ Education Plus - 5,000+ students managed
✅ Health First Clinic - Seamless patient management

Your success story could be next.

#Magala #Business #Entrepreneurship #DOBiz #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p4_magala_sme_9e07f17c.png",
        imagePrompt: "Magala SME success - Earth green imagery with Ethiopian small businesses, entrepreneurs, and prosperity symbols",
        expectedOutcome: "Business engagement, 50K+ impressions, 2.5K+ engagements",
        cta: `💼 Start Your Success: ${ETHIOBIZ_WEBSITE}/magala
📞 ${ETHIOBIZ_PHONE}
🚀 Free Trial: [REGISTER_LINK]`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p5",
        date: "2026-04-15",
        day: "Wednesday",
        platform: ["telegram", "instagram"],
        pillar: "walta",
        contentType: "Support Feature",
        title: "Walta Support: Your Account Security Matters",
        content: `🛡️ WALTA SUPPORT - Account Security Essentials

Walta protects your account with these 5 security features:

1️⃣ Two-Factor Authentication - Extra protection for your login
2️⃣ Strong Password Requirements - Secure by default
3️⃣ Session Management - Control your active devices
4️⃣ Account Recovery - Fast restoration if needed
5️⃣ 24/7 Support Team - Always here to help

Your account security is our top priority. Walta has your back.

#Walta #Support #Security #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p5_walta_security_9dbe1b47.png",
        imagePrompt: "Walta Support - Purple shield protecting account with security features, helpdesk agent, 24/7 support imagery",
        expectedOutcome: "Promote Walta support features, 36K+ impressions, 1.8K+ engagements",
        cta: `🛡️ Enable 2FA: ${ETHIOBIZ_WEBSITE}/walta
📞 Support Team: ${ETHIOBIZ_PHONE}
💬 Telegram: [TELEGRAM_SUPPORT_LINK]
🔔 Subscribe: @EthioBiz_Support`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p6",
        date: "2026-04-16",
        day: "Thursday",
        platform: ["facebook", "instagram"],
        pillar: "general",
        contentType: "Announcement",
        title: "Special Announcement: Influencer Partnership",
        content: `🌟 SPECIAL ANNOUNCEMENT

We're thrilled to announce partnerships with Ethiopia's leading influencers and thought leaders!

Together, we're amplifying the EthioBiz message and reaching millions with our vision of digital transformation.

Influencer Partners Include:
🎤 [INFLUENCER_NAME_1] - Tech & Innovation
🎤 [INFLUENCER_NAME_2] - Business & Entrepreneurship
🎤 [INFLUENCER_NAME_3] - Community & Culture
🎤 [INFLUENCER_NAME_4] - Digital Transformation

Follow them for exclusive EthioBiz content and insights.

#EthioBiz #Influencers #Partnership #Ethiopia #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p6_influencer_announcement_3c7acb35.png",
        imagePrompt: "Influencer partnership announcement - Collaborative imagery with multiple influencers and EthioBiz branding",
        expectedOutcome: "Partnership visibility, 55K+ impressions, 3K+ engagements",
        cta: `🤝 Partner With Us: ${ETHIOBIZ_WEBSITE}/partnerships
📞 ${ETHIOBIZ_PHONE}
💬 Follow: @EthioBiz_Official`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w2p7",
        date: "2026-04-17",
        day: "Friday",
        platform: ["telegram", "facebook"],
        pillar: "afocha",
        contentType: "Community Story",
        title: "Afocha Story: Building Community Together",
        content: `❤️ AFOCHA STORY - Building Community Together

In Ethiopia, we have a saying: "Yetesfa Sefer" (the journey is long, but we walk together).

Afocha is about that spirit of togetherness. It's about recognizing that our strength lies not in individual success, but in collective growth.

This week, we celebrate the communities forming around EthioBiz:
💝 Support groups helping each other learn
🤝 Business networks creating opportunities
❤️ Spiritual circles preserving our heritage
🌍 Global connections bridging continents

Your community awaits.

#Afocha #Community #Together #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w2p7_afocha_community_eefc89f8.png",
        imagePrompt: "Afocha community story - Red heart imagery with diverse Ethiopian people coming together in community",
        expectedOutcome: "Community engagement, 42K+ impressions, 2.2K+ engagements",
        cta: `❤️ Join Community: ${ETHIOBIZ_WEBSITE}/community
📞 ${ETHIOBIZ_PHONE}
🔔 Subscribe: @Afocha_Community`,
        week: 2,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
    ],
  },
  {
    week: 3,
    startDate: "2026-04-18",
    endDate: "2026-04-24",
    theme: "Deep Dive & Empowerment",
    goal: "Official launch announcement, Magala and Dagu features, DOBiz ERP highlights, engagement peak",
    posts: [
      {
        id: "w3p1",
        date: "2026-04-18",
        day: "Saturday",
        platform: ["telegram", "facebook", "instagram"],
        pillar: "general",
        contentType: "Major Announcement",
        title: "🚀 OFFICIAL ETHIOBIZ LAUNCH - LIVE NOW",
        content: `🚀 ETHIOBIZ IS OFFICIALLY LIVE

Today marks a historic moment. EthioBiz—the unified digital ecosystem rooted in Ethiopia's heritage—is now live and accessible to all.

After months of development, we're proud to present:

✅ Tibeb (Soul) - Spiritual connection and heritage
✅ Dagu (Mind) - Verified learning and wisdom
✅ Magala (Body) - Marketplace and prosperity
✅ Walta (Self) - Digital security and protection
✅ Afocha (Heart) - Community and connection

Plus: DOBiz Smart ERP, Jobs Portal, Shop Marketplace, and Hadeeda BizAI

Join millions of Ethiopians building the future together.

#EthioBizLaunch #OneEthiopia #DigitalFuture #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w3p1_official_launch_ff87313a.png",
        imagePrompt: "Official EthioBiz launch - Grand celebration imagery with all five pillars, Ethiopian flag, and digital elements",
        expectedOutcome: "Major launch announcement, 100K+ impressions, 5K+ engagements, 1K+ signups",
        cta: `🚀 Launch Now: ${ETHIOBIZ_WEBSITE}
📞 ${ETHIOBIZ_PHONE}
💬 Join: @EthioBiz_Official`,
        week: 3,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w3p2",
        date: "2026-04-19",
        day: "Sunday",
        platform: ["instagram", "facebook"],
        pillar: "magala",
        contentType: "Product Feature",
        title: "DOBiz Smart ERP - Your Business Transformation Starts Here",
        content: `💼 DOBIZ SMART ERP - Transform Your Business

Introducing DOBiz Smart ERP—the cloud-based business management system designed specifically for Ethiopian enterprises.

DOBiz Modules:
🏠 DOBiz Home - Personal & home business operations
🛍️ DOBiz Retail - Shop inventory & sales management
🔧 DOBiz Service - Service provider scheduling
📚 DOBiz Education - School & institution management
🏭 DOBiz Manufacturing - Production & supply chain
🏥 DOBiz Health - Healthcare clinic management

Powered by Hadeeda BizAI - Your 24/7 business assistant

Start your free 1-week trial today. No credit card required.

#DOBiz #ERP #Business #Entrepreneurship #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w3p2_dobiz_erp_d064f2f6.png",
        imagePrompt: "DOBiz Smart ERP feature - Modern business dashboard with Ethiopian elements and all six modules visualized",
        expectedOutcome: "DOBiz awareness, 65K+ impressions, 3.5K+ engagements, 800+ trial signups",
        cta: `💼 Start Free Trial: ${ETHIOBIZ_WEBSITE}/magala
📞 ${ETHIOBIZ_PHONE}
🤖 Ask Hadeeda: [HADEEDA_LINK]`,
        week: 3,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w3p3",
        date: "2026-04-20",
        day: "Monday",
        platform: ["telegram", "facebook"],
        pillar: "dagu",
        contentType: "Feature Launch",
        title: "Dagu Daily Bot - Your Personal Learning Assistant",
        content: `🤖 DAGU DAILY BOT - Your Personal Learning Assistant

Meet Dagu Daily Bot—your AI-powered learning companion on Telegram.

Every morning, receive:
📚 Daily Lesson - Bite-sized knowledge on business, skills, and wisdom
🎯 Challenge of the Day - Test your knowledge
💡 Tip of the Day - Practical advice for success
🏆 Leaderboard - See how you rank among learners

Subscribe now and start your learning journey.

#Dagu #Learning #AI #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w3p3_dagu_daily_bot_efea6886.png",
        imagePrompt: "Dagu Daily Bot - Indigo blue AI assistant imagery with learning symbols and daily notification elements",
        expectedOutcome: "Bot adoption, 45K+ impressions, 2.5K+ bot subscriptions",
        cta: `🤖 Subscribe to Bot: @Dagu_Daily_Bot
📞 ${ETHIOBIZ_PHONE}
📚 Learn More: ${ETHIOBIZ_WEBSITE}/dagu`,
        week: 3,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w3p4",
        date: "2026-04-21",
        day: "Tuesday",
        platform: ["instagram", "facebook"],
        pillar: "walta",
        contentType: "Support Resource",
        title: "Blog: Getting the Most from Walta Support",
        content: `🛡️ NEW BLOG - Your Complete Walta Support Guide

Discover how Walta supports you across all EthioBiz pillars:

📖 Chapter 1: Getting Started with Walta
📖 Chapter 2: Account Security Features
📖 Chapter 3: Using the Helpdesk
📖 Chapter 4: Troubleshooting Common Issues
📖 Chapter 5: Best Practices for Account Protection

Read the guide and maximize your EthioBiz experience.

#Walta #Support #Guide #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w3p4_walta_blog_c793f992.png",
        imagePrompt: "Walta Support Blog - Purple shield with helpdesk agent, support documentation, user guide imagery",
        expectedOutcome: "Promote Walta support resources, 35K+ impressions, 1.5K+ guide downloads",
        cta: `📖 Read Full Guide: ${ETHIOBIZ_WEBSITE}/walta/guide
📞 Support: ${ETHIOBIZ_PHONE}
💬 Telegram: [TELEGRAM_SUPPORT_LINK]
🔔 Subscribe: @EthioBiz_Support`,
        week: 3,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w3p5",
        date: "2026-04-22",
        day: "Wednesday",
        platform: ["telegram", "instagram"],
        pillar: "tibeb",
        contentType: "Testimonial",
        title: "Tibeb Testimonials - Voices of Faith",
        content: `🕌 TIBEB TESTIMONIALS - Voices of Faith

Hear from Ethiopians discovering spiritual connection through Tibeb:

"Tibeb helped me reconnect with my heritage while embracing modern life." - Abebe, Addis Ababa

"The spiritual guidance on Tibeb has transformed my daily practice." - Almaz, Dire Dawa

"Finally, a platform that honors our traditions in the digital age." - Dawit, Hawassa

"I feel part of a global Ethiopian community." - Selam, Diaspora

Your story matters. Share your Tibeb experience with us.

#Tibeb #Testimonials #Faith #Community #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w3p5_tibeb_testimonials_d95de739.png",
        imagePrompt: "Tibeb testimonials - Golden imagery with diverse Ethiopian faces and spiritual connection elements",
        expectedOutcome: "Social proof, 42K+ impressions, 2.2K+ engagements",
        cta: `🕌 Share Your Story: ${ETHIOBIZ_WEBSITE}/tibeb
📞 ${ETHIOBIZ_PHONE}
💬 Join: @Tibeb_Soul`,
        week: 3,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
    ],
  },
  {
    week: 4,
    startDate: "2026-04-25",
    endDate: "2026-05-01",
    theme: "Empowerment, Verification & Anticipation",
    goal: "Final push with Afocha launch, Hadeeda BizAI showcase, Afocha anticipation, campaign recap",
    posts: [
      {
        id: "w4p1",
        date: "2026-04-25",
        day: "Saturday",
        platform: ["telegram", "facebook"],
        pillar: "general",
        contentType: "Explainer Video",
        title: "EthioBiz Explainer Video - One Civilization. Many Paths.",
        content: `🎬 ETHIOBIZ EXPLAINER VIDEO

Watch our comprehensive explainer video to understand the full EthioBiz ecosystem:

🕌 Tibeb - Worship of the Soul
🧠 Dagu - Knowledge of the Mind
💼 Magala - Marketplace of the Body
🛡️ Walta - Securing the Self
❤️ Afocha - Love of the Heart

Plus: DOBiz Smart ERP, Hadeeda BizAI, and more.

3 minutes. Life-changing insights.

#EthioBiz #Explainer #OneEthiopia #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p1_explainer_video_3b924c06.png",
        imagePrompt: "EthioBiz explainer video - Cinematic overview of all five pillars with modern animation and Ethiopian elements",
        expectedOutcome: "Video engagement, 70K+ impressions, 4K+ video views",
        cta: `🎬 Watch Video: ${ETHIOBIZ_WEBSITE}
📞 ${ETHIOBIZ_PHONE}
💬 Share: @EthioBiz_Official`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p2",
        date: "2026-04-26",
        day: "Sunday",
        platform: ["instagram", "facebook"],
        pillar: "dagu",
        contentType: "Feature Highlight",
        title: "Dagu Verified Skill Tree - Earn Your Badge",
        content: `🏆 DAGU VERIFIED SKILL TREE - Earn Your Badge

Introducing Dagu's Verified Skill Tree—a comprehensive learning pathway to mastery.

Complete courses and earn verified badges:
🥉 Bronze Badge - Foundational Skills
🥈 Silver Badge - Intermediate Mastery
🥇 Gold Badge - Expert Level
💎 Platinum Badge - Master Instructor

Each badge is verified and recognized by employers across Ethiopia and beyond.

Start your skill journey today.

#Dagu #Skills #Certification #Learning #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p2_dagu_skills_45226141.png",
        imagePrompt: "Dagu skill tree - Indigo blue badge system with skill progression and achievement elements",
        expectedOutcome: "Skill engagement, 48K+ impressions, 2.5K+ course enrollments",
        cta: `🏆 Start Learning: ${ETHIOBIZ_WEBSITE}/dagu
📞 ${ETHIOBIZ_PHONE}
📚 Browse Courses: [COURSES_LINK]`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p3",
        date: "2026-04-27",
        day: "Monday",
        platform: ["telegram", "facebook"],
        pillar: "magala",
        contentType: "Feature Showcase",
        title: "DOBiz Smart Features - Hadeeda BizAI in Action",
        content: `🤖 DOBIZ SMART FEATURES - Hadeeda BizAI in Action

Hadeeda BizAI transforms how you do business. Watch her in action:

✨ Executive Assistant - Manage your calendar and communications
💡 Strategy & Content - Create marketing strategies in minutes
💰 Sales Agent - Automate sales flows and close deals
📊 Asset Management - Control inventories and finances
🎯 Project Manager - Plan and execute projects flawlessly
🛟 24/7 Support - Always there when you need help

Your business just got smarter.

#DOBiz #Hadeeda #AI #Business #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p3_dobiz_smart_186fe983.png",
        imagePrompt: "DOBiz Smart features - Hadeeda BizAI showcase with all six capabilities visualized in modern interface",
        expectedOutcome: "Feature awareness, 55K+ impressions, 3K+ engagements",
        cta: `🤖 Experience Hadeeda: ${ETHIOBIZ_WEBSITE}/magala
📞 ${ETHIOBIZ_PHONE}
🚀 Start Trial: [REGISTER_LINK]`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p4",
        date: "2026-04-28",
        day: "Tuesday",
        platform: ["instagram", "facebook"],
        pillar: "magala",
        contentType: "Announcement",
        title: "Hadeeda BizAI - Your Business Transformation Partner",
        content: `🤖 HADEEDA BIZAI - Your Business Transformation Partner

Meet Hadeeda—Ethiopia's most sophisticated business intelligence agent.

Hadeeda is trained specifically for the Ethiopian market and understands:
🌍 Local business culture and practices
💼 Multi-industry operations
🎯 Entrepreneurial challenges
📈 Growth opportunities
🤝 Community values

She's not just software. She's your partner in success.

Available 24/7. Ready to transform your business.

#Hadeeda #BizAI #Business #Ethiopia #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p4_hadeeda_bizai_42b36fc6.png",
        imagePrompt: "Hadeeda BizAI - Sophisticated AI agent imagery with Ethiopian business elements and modern technology",
        expectedOutcome: "Hadeeda awareness, 52K+ impressions, 2.8K+ engagements",
        cta: `🤖 Meet Hadeeda: ${ETHIOBIZ_WEBSITE}/magala
📞 ${ETHIOBIZ_PHONE}
💬 Chat Now: [HADEEDA_CHAT]`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p5",
        date: "2026-04-29",
        day: "Wednesday",
        platform: ["telegram", "instagram"],
        pillar: "afocha",
        contentType: "Launch Teaser",
        title: "Afocha Coming Soon - Love of the Heart",
        content: `❤️ AFOCHA COMING SOON - Love of the Heart

The final pillar is almost here. Afocha—Love of the Heart—is launching next week.

Get ready for:
💝 Community Connection Tools
🤝 Collective Support Features
❤️ Shared Values Platform
🌍 Global Community Network

Afocha will transform how we connect, support, and grow together.

Mark your calendars. The heart of EthioBiz is coming.

#Afocha #Community #Love #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p5_afocha_launch_4434d14c.png",
        imagePrompt: "Afocha launch teaser - Red heart imagery with anticipation elements and community connection symbols",
        expectedOutcome: "Anticipation building, 45K+ impressions, 2.2K+ engagements",
        cta: `❤️ Get Ready: ${ETHIOBIZ_WEBSITE}/afocha
📞 ${ETHIOBIZ_PHONE}
🔔 Notify Me: [NOTIFY_LINK]`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p6",
        date: "2026-04-30",
        day: "Thursday",
        platform: ["facebook", "instagram"],
        pillar: "tibeb",
        contentType: "Live Event",
        title: "Tibeb Live Q&A - Ask the Experts",
        content: `🕌 TIBEB LIVE Q&A - Ask the Experts

Join us for a live Q&A session with Tibeb experts and spiritual leaders.

Topics:
🕌 Preserving Ethiopian spiritual heritage in the digital age
🙏 Integrating traditional wisdom with modern life
💫 Building spiritual community online
🌟 The role of faith in entrepreneurship

Live on Facebook & Instagram
Time: [TIME_TO_BE_ANNOUNCED]

Your questions. Expert answers. Live.

#Tibeb #LiveQA #Spirituality #Heritage #EthioBiz #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p6_tibeb_live_qa_879517a8.png",
        imagePrompt: "Tibeb live Q&A - Golden imagery with spiritual leaders and live event elements",
        expectedOutcome: "Live engagement, 50K+ impressions, 3K+ live viewers",
        cta: `🕌 Join Live: ${ETHIOBIZ_WEBSITE}/live
📞 ${ETHIOBIZ_PHONE}
💬 Ask Question: [LIVE_LINK]`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
      {
        id: "w4p7",
        date: "2026-05-01",
        day: "Friday",
        platform: ["telegram", "facebook", "instagram"],
        pillar: "general",
        contentType: "Campaign Recap",
        title: "🎉 Campaign Recap - One Month of Transformation",
        content: `🎉 CAMPAIGN RECAP - One Month of Transformation

What an incredible journey! In just one month, we've launched EthioBiz and touched millions of lives.

Campaign Highlights:
📊 1M+ Impressions
🤝 50K+ Engagements
🚀 25K+ Website Visits
💼 500+ DOBiz ERP Signups
🕌 Tibeb Community: 15K+ Members
🧠 Dagu Learners: 12K+ Enrolled
💰 Magala Businesses: 50+ Active
🛡️ Walta Users: 8K+ Secured
❤️ Afocha Ready: Launch Next Week

Thank you for being part of this vision.

#EthioBizCampaign #OneEthiopia #DigitalFuture #InShaAllah`,
        imageUrl: "https://d2xsxph8kpxj0f.cloudfront.net/310519663514420600/4rkb9Du77yDf2a5ivFHFXC/ethiobiz_w4p7_recap_a1fa84e8.png",
        imagePrompt: "Campaign recap - Celebratory imagery with all five pillars, statistics, and success elements",
        expectedOutcome: "Campaign closure, 80K+ impressions, 4K+ engagements",
        cta: `🚀 Continue Journey: ${ETHIOBIZ_WEBSITE}
📞 ${ETHIOBIZ_PHONE}
💬 Join: @EthioBiz_Official`,
        week: 4,
        phone: ETHIOBIZ_PHONE,
        website: ETHIOBIZ_WEBSITE,
      },
    ],
  },
];

const = {
  impressions: { label: "Total Impressions", target: "1,000,000+", metric: "👁️" },
  engagements: { label: "Total Engagements", target: "50,000+", metric: "💬" },
  visits: { label: "Website Visits", target: "25,000+", metric: "🌐" },
  dobiz: { label: "DOBiz ERP Signups", target: "500+", metric: "💼" },
  tibeb: { label: "Tibeb Members", target: "15,000+", metric: "🕌" },
  dagu: { label: "Dagu Learners", target: "12,000+", metric: "🧠" },
  magala: { label: "Magala Businesses", target: "50+", metric: "💼" },
  walta: { label: "Walta Users", target: "8,000+", metric: "🔐" },
  afocha: { label: "Afocha Community", target: "20,000+", metric: "❤️" },
  telegram: { label: "Telegram Followers", target: "30,000+", metric: "✈️" },
  facebook: { label: "Facebook Followers", target: "25,000+", metric: "f" },
};

    const fs = require('fs');
    fs.writeFileSync('C:\\Users\\bizit\\OneDrive\\Documents\\BISMALLAH BIZ PROJECTS INSHA'ALLAH\\BISMALLAH ETHIOBIZ INSHA'ALLAH\\BISMALLAH ETHIOBIZ INSTALLATION INSHA'ALLAH\\BISMALLAH ETHIBIZ STAGING INSHA'ALLAH\\bizmarketing\\campaign_data.json', JSON.stringify({
        campaignWeeks: campaignWeeks
    }, null, 2));
    