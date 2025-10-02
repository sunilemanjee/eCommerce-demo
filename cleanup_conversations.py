#!/usr/bin/env python3
"""
Script to fetch and delete Kibana Agent Builder conversations.
This script reads the KIBANA_URL from environment variables and performs the following:
1. Fetches all conversations from GET kbn:/api/agent_builder/conversations
2. Deletes each conversation using DELETE kbn:/api/agent_builder/conversations/{id}
"""

import os
import sys
import requests
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from variables.env file."""
    env_file = os.path.join(os.path.dirname(__file__), 'variables.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        print(f"Warning: {env_file} not found. Using system environment variables.")
    
    kibana_url = os.getenv('KIBANA_URL')
    api_key = os.getenv('ES_API_KEY')
    
    if not kibana_url:
        print("Error: KIBANA_URL environment variable not found.")
        sys.exit(1)
    
    if not api_key:
        print("Error: ES_API_KEY environment variable not found.")
        sys.exit(1)
    
    return kibana_url, api_key

def get_conversations(kibana_url: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all conversations from the Kibana Agent Builder API.
    
    Args:
        kibana_url: The base Kibana URL
        api_key: The API key for authentication
        
    Returns:
        List of conversation objects
    """
    url = f"{kibana_url}/api/agent_builder/conversations"
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'Content-Type': 'application/json',
        'kbn-xsrf': 'true'
    }
    
    try:
        print(f"Fetching conversations from: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        conversations = response.json()
        print(f"Found {len(conversations)} conversations")
        return conversations
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching conversations: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        sys.exit(1)

def delete_conversation(kibana_url: str, conversation_id: str, api_key: str) -> bool:
    """
    Delete a specific conversation by ID.
    
    Args:
        kibana_url: The base Kibana URL
        conversation_id: The ID of the conversation to delete
        api_key: The API key for authentication
        
    Returns:
        True if successful, False otherwise
    """
    url = f"{kibana_url}/api/agent_builder/conversations/{conversation_id}"
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'Content-Type': 'application/json',
        'kbn-xsrf': 'true'
    }
    
    try:
        print(f"Deleting conversation: {conversation_id}")
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        print(f"Successfully deleted conversation: {conversation_id}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return False

def check_permissions(kibana_url: str, api_key: str) -> bool:
    """
    Check if the API key has the required permissions for Agent Builder.
    
    Args:
        kibana_url: The base Kibana URL
        api_key: The API key for authentication
        
    Returns:
        True if permissions are sufficient, False otherwise
    """
    url = f"{kibana_url}/api/agent_builder/conversations"
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'Content-Type': 'application/json',
        'kbn-xsrf': 'true'
    }
    
    try:
        print("Checking API key permissions...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✓ API key has sufficient permissions")
            return True
        elif response.status_code == 403:
            print("✗ API key lacks required permissions")
            print(f"Response body: {response.text}")
            print("Error: The API key needs the 'read_onechat' privilege for Kibana Agent Builder")
            print("\nTo fix this, you need to:")
            print("1. Create a new API key with the following role:")
            print("   - Add 'applications' section with 'read_onechat' privilege")
            print("2. Or modify your existing role to include:")
            print("   'applications': [{'application': 'kibana-.kibana', 'privileges': ['read_onechat']}]")
            return False
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error checking permissions: {e}")
        return False

def main():
    """Main function to orchestrate the conversation cleanup process."""
    print("Starting Kibana Agent Builder conversation cleanup...")
    
    # Load environment variables
    kibana_url, api_key = load_environment()
    print(f"Using Kibana URL: {kibana_url}")
    
    # Check permissions first
    if not check_permissions(kibana_url, api_key):
        print("\nCannot proceed without proper permissions.")
        print("Please create a new API key with the required privileges and update your variables.env file.")
        return
    
    # Fetch all conversations
    conversations = get_conversations(kibana_url, api_key)
    
    if not conversations:
        print("No conversations found to delete.")
        return
    
    # Display conversations that will be deleted
    print("\nConversations to be deleted:")
    for i, conv in enumerate(conversations, 1):
        print(f"{i}. ID: {conv.get('id', 'N/A')}")
        print(f"   Title: {conv.get('title', 'N/A')}")
        print(f"   Agent ID: {conv.get('agent_id', 'N/A')}")
        print(f"   User: {conv.get('user', {}).get('username', 'N/A')}")
        print(f"   Created: {conv.get('created_at', 'N/A')}")
        print()
    
    # Ask for confirmation
    confirm = input(f"Are you sure you want to delete all {len(conversations)} conversations? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    # Delete each conversation
    print("\nStarting deletion process...")
    successful_deletions = 0
    failed_deletions = 0
    
    for conv in conversations:
        conversation_id = conv.get('id')
        if not conversation_id:
            print(f"Warning: Conversation missing ID, skipping: {conv}")
            failed_deletions += 1
            continue
            
        if delete_conversation(kibana_url, conversation_id, api_key):
            successful_deletions += 1
        else:
            failed_deletions += 1
    
    # Summary
    print(f"\nCleanup completed!")
    print(f"Successfully deleted: {successful_deletions} conversations")
    print(f"Failed to delete: {failed_deletions} conversations")

if __name__ == "__main__":
    main()
