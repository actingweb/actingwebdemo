"""
Shared MCP tools for ActingWeb demo applications.

This module provides reusable MCP tool implementations that can be shared
across different ActingWeb demo applications (FastAPI and Flask).
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# We'll import ActorInterface when needed to avoid circular imports
logger = logging.getLogger(__name__)


def search_actor_data(actor, query: str, search_type: str = "all", limit: int = 10) -> Dict[str, Any]:
    """
    Search through all stored actor data.
    
    Args:
        actor: Actor instance to search
        query: Search query string
        search_type: Type of data to search ("all", "notes", "reminders", "properties")
        limit: Maximum number of results
        
    Returns:
        Search results dictionary
    """
    query = query.strip().lower()
    if not query:
        return {"error": "Search query cannot be empty"}
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    results = []
    
    # Search notes
    if search_type in ["all", "notes"] and actor.properties:
        notes = actor.properties.get("notes", [])
        for note in notes:
            # Check if query matches title, content, or tags
            title_match = query in note.get("title", "").lower()
            content_match = query in note.get("content", "").lower()
            tag_match = any(query in tag.lower() for tag in note.get("tags", []))
            
            if title_match or content_match or tag_match:
                results.append({
                    "type": "note",
                    "id": note.get("id"),
                    "title": note.get("title"),
                    "content": note.get("content")[:200] + "..." if len(note.get("content", "")) > 200 else note.get("content"),
                    "tags": note.get("tags", []),
                    "priority": note.get("priority"),
                    "created_at": note.get("created_at")
                })
    
    # Search reminders
    if search_type in ["all", "reminders"] and actor.properties:
        reminders = actor.properties.get("reminders", [])
        for reminder in reminders:
            # Check if query matches title or description
            title_match = query in reminder.get("title", "").lower()
            desc_match = query in reminder.get("description", "").lower()
            
            if title_match or desc_match:
                results.append({
                    "type": "reminder",
                    "id": reminder.get("id"),
                    "title": reminder.get("title"),
                    "description": reminder.get("description"),
                    "due_date": reminder.get("due_date"),
                    "priority": reminder.get("priority"),
                    "category": reminder.get("category"),
                    "completed": reminder.get("completed", False),
                    "created_at": reminder.get("created_at")
                })
    
    # Search other properties
    if search_type in ["all", "properties"] and actor.properties:
        # Search through other stored properties for matches
        for key, value in actor.properties.get("custom_data", {}).items():
            if isinstance(value, str) and query in value.lower():
                results.append({
                    "type": "property",
                    "key": key,
                    "value": value[:200] + "..." if len(str(value)) > 200 else str(value)
                })
    
    # Limit results
    results = results[:limit]
    
    logger.info(f"MCP Tool: Found {len(results)} items matching '{query}' in {search_type}")
    
    return {
        "status": "success",
        "query": query,
        "search_type": search_type,
        "results": results,
        "total_found": len(results)
    }


def fetch_actor_data(actor, fetch_type: str, item_id: Optional[int] = None, 
                    limit: int = 20, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch specific data items or collections.
    
    Args:
        actor: Actor instance to fetch from
        fetch_type: Type of data to fetch
        item_id: Specific ID to fetch (for individual items)
        limit: Maximum number of items for collections
        filters: Optional filters for collections
        
    Returns:
        Fetch results dictionary
    """
    if not filters:
        filters = {}
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    if not actor.properties:
        return {"error": "Actor properties not available"}
    
    # Fetch specific note
    if fetch_type == "note":
        if not item_id:
            return {"error": "ID is required for fetching specific note"}
        
        notes = actor.properties.get("notes", [])
        note = next((n for n in notes if n.get("id") == item_id), None)
        
        if not note:
            return {"error": f"Note with ID {item_id} not found"}
        
        logger.info(f"MCP Tool: Fetched note {item_id}")
        return {"status": "success", "type": "note", "data": note}
    
    # Fetch specific reminder
    elif fetch_type == "reminder":
        if not item_id:
            return {"error": "ID is required for fetching specific reminder"}
        
        reminders = actor.properties.get("reminders", [])
        reminder = next((r for r in reminders if r.get("id") == item_id), None)
        
        if not reminder:
            return {"error": f"Reminder with ID {item_id} not found"}
        
        logger.info(f"MCP Tool: Fetched reminder {item_id}")
        return {"status": "success", "type": "reminder", "data": reminder}
    
    # Fetch all notes
    elif fetch_type == "notes_all":
        notes = actor.properties.get("notes", [])
        
        # Apply tag filter if specified
        if filters.get("tag"):
            tag_filter = filters["tag"].lower()
            notes = [n for n in notes if tag_filter in [t.lower() for t in n.get("tags", [])]]
        
        # Apply priority filter if specified
        if filters.get("priority"):
            notes = [n for n in notes if n.get("priority") == filters["priority"]]
        
        # Limit results
        notes = notes[:limit]
        
        logger.info(f"MCP Tool: Fetched {len(notes)} notes")
        return {"status": "success", "type": "notes_collection", "data": notes, "total_count": len(notes)}
    
    # Fetch all reminders
    elif fetch_type == "reminders_all":
        reminders = actor.properties.get("reminders", [])
        
        # Apply completion filter if specified
        if "completed" in filters:
            reminders = [r for r in reminders if r.get("completed", False) == filters["completed"]]
        
        # Apply priority filter if specified
        if filters.get("priority"):
            reminders = [r for r in reminders if r.get("priority") == filters["priority"]]
        
        # Limit results
        reminders = reminders[:limit]
        
        logger.info(f"MCP Tool: Fetched {len(reminders)} reminders")
        return {"status": "success", "type": "reminders_collection", "data": reminders, "total_count": len(reminders)}
    
    # Fetch usage statistics
    elif fetch_type == "stats":
        notes = actor.properties.get("notes", [])
        reminders = actor.properties.get("reminders", [])
        mcp_usage = actor.properties.get("mcp_usage_count", 0)
        
        # Calculate tag usage
        tag_counts: Dict[str, int] = {}
        for note in notes:
            for tag in note.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        stats = {
            "mcp_usage_count": mcp_usage,
            "total_notes": len(notes),
            "total_reminders": len(reminders),
            "pending_reminders": len([r for r in reminders if not r.get("completed", False)]),
            "completed_reminders": len([r for r in reminders if r.get("completed", False)]),
            "most_used_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "actor_id": actor.id,
            "created_at": actor.properties.get("created_at", "unknown")
        }
        
        logger.info(f"MCP Tool: Fetched usage statistics")
        return {"status": "success", "type": "statistics", "data": stats}
    
    # Fetch recent items
    elif fetch_type == "recent":
        notes = actor.properties.get("notes", [])
        reminders = actor.properties.get("reminders", [])
        
        # Get recent notes (last 5)
        recent_notes = sorted(notes, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        
        # Get recent reminders (last 5)
        recent_reminders = sorted(reminders, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        
        logger.info(f"MCP Tool: Fetched recent items")
        return {
            "status": "success",
            "type": "recent_items",
            "data": {"recent_notes": recent_notes, "recent_reminders": recent_reminders}
        }
    
    else:
        return {"error": f"Unknown fetch type: {fetch_type}"}


def create_note(actor, title: str, content: str, tags: Optional[List[str]] = None, 
               priority: str = "medium") -> Dict[str, Any]:
    """
    Create and store a note.
    
    Args:
        actor: Actor instance to store note in
        title: Note title
        content: Note content
        tags: Optional tags list
        priority: Priority level
        
    Returns:
        Creation result dictionary
    """
    if not title.strip() or not content.strip():
        return {"error": "Both title and content are required"}
    
    if not tags:
        tags = []
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
        # Store note in actor properties
        notes = actor.properties.get("notes", [])
        note = {
            "id": len(notes) + 1,
            "title": title.strip(),
            "content": content.strip(),
            "tags": tags,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        notes.append(note)
        actor.properties.notes = notes
        
        logger.info(f"MCP Tool: Created note '{title}' with {len(tags)} tags")
        
        return {
            "status": "created",
            "note_id": note["id"],
            "title": title,
            "tags": tags,
            "priority": priority,
            "total_notes": len(notes)
        }
    else:
        return {"error": "Actor properties not available"}


def create_reminder(actor, title: str, due_date: str, description: str = "", 
                   priority: str = "medium", category: str = "general") -> Dict[str, Any]:
    """
    Create a time-based reminder.
    
    Args:
        actor: Actor instance to store reminder in
        title: Reminder title
        due_date: Due date string
        description: Optional description
        priority: Priority level
        category: Category for organization
        
    Returns:
        Creation result dictionary
    """
    if not title.strip() or not due_date.strip():
        return {"error": "Both title and due_date are required"}
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
        # Parse due date (simplified - in real app would use dateutil)
        try:
            # Try to parse ISO format first
            if due_date.count("-") == 2 and len(due_date) >= 10:
                parsed_date = datetime.fromisoformat(due_date[:10])
            else:
                # For natural language, store as-is for now
                parsed_date = None
            created_at = datetime.now().isoformat()
        except:
            parsed_date = None
            created_at = None
        
        # Store reminder in actor properties
        reminders = actor.properties.get("reminders", [])
        reminder = {
            "id": len(reminders) + 1,
            "title": title.strip(),
            "description": description.strip(),
            "due_date": due_date.strip(),
            "parsed_date": parsed_date.isoformat() if parsed_date else None,
            "priority": priority,
            "category": category,
            "completed": False,
            "created_at": created_at
        }
        reminders.append(reminder)
        actor.properties.reminders = reminders
        
        logger.info(f"MCP Tool: Created {priority} priority reminder '{title}' due {due_date}")
        
        return {
            "status": "created",
            "reminder_id": reminder["id"],
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "total_reminders": len(reminders)
        }
    else:
        return {"error": "Actor properties not available"}