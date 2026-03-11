use hdk::prelude::*;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AgentProfile {
    pub agent_pubkey: AgentPubKey,
    pub username: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub capabilities: Vec<String>,
    pub reputation: f64,
    pub created_at: u64,
    pub last_active: u64,
    pub metadata: BTreeMap<String, String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateProfileInput {
    pub username: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub capabilities: Vec<String>,
    pub metadata: BTreeMap<String, String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct UpdateProfileInput {
    pub display_name: Option<String>,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub capabilities: Option<Vec<String>>,
    pub metadata: Option<BTreeMap<String, String>>,
}

#[hdk_entry_helper]
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProfileEntry {
    pub agent_pubkey: AgentPubKey,
    pub username: String,
    pub display_name: String,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub capabilities: Vec<String>,
    pub reputation: f64,
    pub created_at: u64,
    pub last_active: u64,
    pub metadata: BTreeMap<String, String>,
}

#[hdk_entry_helper]
#[derive(Serialize, Deserialize, Debug)]
pub struct CapabilityGrant {
    pub granter: AgentPubKey,
    pub grantee: AgentPubKey,
    pub capability: String,
    pub granted_at: u64,
    pub expires_at: Option<u64>,
}

#[hdk_extern]
pub fn create_profile(input: CreateProfileInput) -> ExternResult<EntryHash> {
    let agent_info = agent_info()?;
    let agent_pubkey = agent_info.agent_latest_pubkey;
    
    // Check if profile already exists
    let profile = get_profile(&agent_pubkey)?;
    if profile.is_some() {
        return Err("Profile already exists for this agent".into());
    }
    
    let now = sys_time()?;
    
    let profile_entry = ProfileEntry {
        agent_pubkey: agent_pubkey.clone(),
        username: input.username.clone(),
        display_name: input.display_name.clone(),
        avatar_url: input.avatar_url.clone(),
        bio: input.bio.clone(),
        capabilities: input.capabilities.clone(),
        reputation: 50.0, // Start with neutral reputation
        created_at: now,
        last_active: now,
        metadata: input.metadata.clone(),
    };
    
    // Create profile entry
    let profile_hash = create_entry(&Entry::App(profile_entry.clone()))?;
    
    // Link from agent pubkey to profile
    create_link(
        agent_pubkey.clone(),
        profile_hash.clone(),
        LinkTag::new("profile")?,
    )?;
    
    // Link from username to profile for lookup
    create_link(
        LinkTag::new(input.username)?,
        profile_hash.clone(),
        LinkTag::new("username")?,
    )?;
    
    // Create capability grants
    for capability in &input.capabilities {
        let grant = CapabilityGrant {
            granter: agent_pubkey.clone(),
            grantee: agent_pubkey.clone(),
            capability: capability.clone(),
            granted_at: now,
            expires_at: None,
        };
        
        let grant_hash = create_entry(&Entry::App(grant))?;
        create_link(
            agent_pubkey.clone(),
            grant_hash,
            LinkTag::new("capability")?,
        )?;
    }
    
    Ok(profile_hash)
}

#[hdk_extern]
pub fn update_profile(input: UpdateProfileInput) -> ExternResult<EntryHash> {
    let agent_info = agent_info()?;
    let agent_pubkey = agent_info.agent_latest_pubkey;
    
    // Get existing profile
    let profile = get_profile(&agent_pubkey)?
        .ok_or("Profile not found")?;
    
    let mut updated_profile = profile;
    
    // Update fields
    if let Some(display_name) = input.display_name {
        updated_profile.display_name = display_name;
    }
    
    if let Some(avatar_url) = input.avatar_url {
        updated_profile.avatar_url = Some(avatar_url);
    }
    
    if let Some(bio) = input.bio {
        updated_profile.bio = Some(bio);
    }
    
    if let Some(capabilities) = input.capabilities {
        updated_profile.capabilities = capabilities;
    }
    
    if let Some(metadata) = input.metadata {
        updated_profile.metadata = metadata;
    }
    
    updated_profile.last_active = sys_time()?;
    
    // Update profile entry
    let profile_hash = update_entry(profile_hash(&updated_profile)?)?;
    
    Ok(profile_hash)
}

#[hdk_extern]
pub fn get_profile(agent_pubkey: AgentPubKey) -> ExternResult<Option<ProfileEntry>> {
    let links = get_links(
        agent_pubkey,
        Some(LinkTag::new("profile")?),
    )?;
    
    if links.is_empty() {
        return Ok(None);
    }
    
    let latest_link = links.into_iter()
        .max_by_key(|link| link.timestamp)
        .ok_or("No profile link found")?;
    
    let profile: ProfileEntry = get(latest_link.target, GetOptions::default())?
        .ok_or("Profile entry not found")?
        .into()
        .ok_or("Expected App entry")?;
    
    Ok(Some(profile))
}

#[hdk_extern]
pub fn get_profile_by_username(username: String) -> ExternResult<Option<ProfileEntry>> {
    let links = get_links(
        LinkTag::new(username)?,
        Some(LinkTag::new("username")?),
    )?;
    
    if links.is_empty() {
        return Ok(None);
    }
    
    let profile_link = links.into_iter().next()
        .ok_or("No profile link found")?;
    
    let profile: ProfileEntry = get(profile_link.target, GetOptions::default())?
        .ok_or("Profile entry not found")?
        .into()
        .ok_or("Expected App entry")?;
    
    Ok(Some(profile))
}

#[hdk_extern]
pub fn search_profiles(query: String) -> ExternResult<Vec<ProfileEntry>> {
    let all_profiles = query_all_profiles()?;
    
    let filtered_profiles = all_profiles
        .into_iter()
        .filter(|profile| {
            profile.username.to_lowercase().contains(&query.to_lowercase()) ||
            profile.display_name.to_lowercase().contains(&query.to_lowercase()) ||
            profile.bio.as_ref()
                .map(|bio| bio.to_lowercase().contains(&query.to_lowercase()))
                .unwrap_or(false)
        })
        .collect();
    
    Ok(filtered_profiles)
}

#[hdk_extern]
pub fn grant_capability(grantee: AgentPubKey, capability: String) -> ExternResult<EntryHash> {
    let agent_info = agent_info()?;
    let granter = agent_info.agent_latest_pubkey;
    
    let now = sys_time()?;
    
    let grant = CapabilityGrant {
        granter: granter.clone(),
        grantee: grantee.clone(),
        capability: capability.clone(),
        granted_at: now,
        expires_at: None,
    };
    
    let grant_hash = create_entry(&Entry::App(grant))?;
    
    // Link from granter to grant
    create_link(
        granter,
        grant_hash.clone(),
        LinkTag::new("granted_capability")?,
    )?;
    
    // Link from grantee to grant
    create_link(
        grantee,
        grant_hash,
        LinkTag::new("received_capability")?,
    )?;
    
    Ok(grant_hash)
}

#[hdk_extern]
pub fn revoke_capability(grant_hash: EntryHash) -> ExternResult<()> {
    // Delete the capability grant entry
    delete_entry(grant_hash)?;
    
    // Also delete associated links
    let links = get_links(
        grant_hash,
        None,
    )?;
    
    for link in links {
        delete_link(link.create_link_hash)?;
    }
    
    Ok(())
}

#[hdk_extern]
pub fn get_agent_capabilities(agent_pubkey: AgentPubKey) -> ExternResult<Vec<String>> {
    let profile = get_profile(agent_pubkey)?;
    
    match profile {
        Some(profile) => Ok(profile.capabilities),
        None => Ok(vec![]),
    }
}

#[hdk_extern]
pub fn update_reputation(agent_pubkey: AgentPubKey, delta: f64) -> ExternResult<EntryHash> {
    let mut profile = get_profile(&agent_pubkey)?
        .ok_or("Profile not found")?;
    
    // Update reputation with bounds checking
    profile.reputation = (profile.reputation + delta).max(0.0).min(100.0);
    profile.last_active = sys_time()?;
    
    let profile_hash = update_entry(profile_hash(&profile)?)?;
    
    Ok(profile_hash)
}

#[hdk_extern]
pub fn get_all_profiles() -> ExternResult<Vec<ProfileEntry>> {
    query_all_profiles()
}

fn query_all_profiles() -> ExternResult<Vec<ProfileEntry>> {
    let query = Query::new();
    let query_result = query.run()?;
    
    let mut profiles = Vec::new();
    for element in query_result {
        if let Ok(profile) = element.clone().try_into() {
            profiles.push(profile);
        }
    }
    
    Ok(profiles)
}

fn profile_hash(profile: &ProfileEntry) -> ExternResult<EntryHash> {
    hash_entry(profile)
}
