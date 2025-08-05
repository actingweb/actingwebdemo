"""
Shared MCP prompts for ActingWeb demo applications.

This module provides reusable MCP prompt implementations that can be shared
across different ActingWeb demo applications (FastAPI and Flask).
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_notes_analysis_prompt(actor, analysis_type: str = "summary", 
                                 tag_filter: str = "", time_period: str = "all_time") -> str:
    """
    Generate analysis prompt based on stored notes.
    
    Args:
        actor: Actor instance containing notes
        analysis_type: Type of analysis ("summary", "trends", "actionable_items", "priorities")
        tag_filter: Optional tag to filter notes
        time_period: Time period for analysis
        
    Returns:
        Generated prompt string
    """
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
        
        # Get notes data for context
        notes = actor.properties.get("notes", [])
        note_count = len(notes)
        
        # Filter by tag if specified
        if tag_filter:
            notes = [n for n in notes if tag_filter.lower() in [tag.lower() for tag in n.get("tags", [])]]
        
        # Generate analysis prompt based on type
        if analysis_type == "summary":
            prompt = f"Please analyze and summarize the following {len(notes)} notes"
            if tag_filter:
                prompt += f" tagged with '{tag_filter}'"
            prompt += f" from {time_period.replace('_', ' ')}. Provide key themes, main topics discussed, and overall patterns you observe.\n\n"
        
        elif analysis_type == "trends":
            prompt = f"Analyze the following {len(notes)} notes for trends and patterns"
            if tag_filter:
                prompt += f" in the '{tag_filter}' category"
            prompt += f". Look for recurring themes, evolving ideas, and progression of thoughts over time.\n\n"
        
        elif analysis_type == "actionable_items":
            prompt = f"Review the following {len(notes)} notes and extract actionable items, tasks, and next steps that should be prioritized. Format as a prioritized list with explanations.\n\n"
        
        elif analysis_type == "priorities":
            prompt = f"Analyze the following {len(notes)} notes to identify the most important and urgent items. Help prioritize what should be focused on first.\n\n"
        
        else:
            prompt = f"Please analyze the following {len(notes)} notes and provide insights:\n\n"
        
        # Add note data to prompt
        for i, note in enumerate(notes[:10], 1):  # Limit to 10 notes to avoid too long prompts
            prompt += f"Note {i}:\n"
            prompt += f"Title: {note.get('title', 'Untitled')}\n"
            prompt += f"Content: {note.get('content', '')}\n"
            prompt += f"Tags: {', '.join(note.get('tags', []))}\n"
            prompt += f"Priority: {note.get('priority', 'medium')}\n\n"
        
        if len(notes) > 10:
            prompt += f"... and {len(notes) - 10} more notes with similar content patterns.\n\n"
        
        prompt += (
            f"Based on this data, please provide a {analysis_type} analysis with specific insights and recommendations."
        )
        
        logger.info(f"MCP Prompt: Generated {analysis_type} analysis for {len(notes)} notes")
        
        return prompt
    else:
        return "Actor properties not available for analysis."


def generate_learning_prompt(actor, topic: str, learning_style: str = "beginner",
                           focus_area: str = "overview", format_type: str = "explanation") -> str:
    """
    Generate a learning-focused prompt.
    
    Args:
        actor: Actor instance (for usage tracking)
        topic: The topic to learn about
        learning_style: Learning approach level
        focus_area: Specific aspect to focus on
        format_type: Preferred response format
        
    Returns:
        Generated learning prompt string
    """
    if not topic.strip():
        return "Please provide a topic to learn about."
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Build learning prompt based on parameters
    prompt = f"I want to learn about {topic} at a {learning_style} level"
    
    if focus_area == "overview":
        prompt += f". Please provide a comprehensive overview covering the key concepts, fundamentals, and why this topic is important."
    elif focus_area == "implementation":
        prompt += f". Focus on practical implementation details, step-by-step processes, and hands-on aspects."
    elif focus_area == "best_practices":
        prompt += f". Emphasize best practices, common patterns, and recommendations from experts in the field."
    elif focus_area == "troubleshooting":
        prompt += f". Focus on common problems, debugging techniques, and solutions to typical challenges."
    else:
        prompt += f" with a focus on {focus_area}."
    
    if format_type == "tutorial":
        prompt += " Present this as a step-by-step tutorial with clear instructions."
    elif format_type == "examples":
        prompt += " Include plenty of concrete examples and code samples where applicable."
    elif format_type == "comparison":
        prompt += " Compare different approaches, tools, or methods related to this topic."
    else:
        prompt += f" Present this as a clear {format_type} with practical insights."
    
    prompt += (
        f" Please structure your response to be educational and actionable for someone at the {learning_style} level."
    )
    
    logger.info(f"MCP Prompt: Generated {learning_style} learning prompt for '{topic}'")
    
    return prompt


def generate_meeting_prep_prompt(actor, meeting_title: str, meeting_type: str = "general",
                               participants: str = "", duration: str = "1 hour", 
                               key_topics: str = "") -> str:
    """
    Generate meeting preparation prompt.
    
    Args:
        actor: Actor instance containing relevant context
        meeting_title: Title or subject of the meeting
        meeting_type: Type of meeting
        participants: List of participants
        duration: Expected duration
        key_topics: Main topics to cover
        
    Returns:
        Generated meeting prep prompt string
    """
    if not meeting_title.strip():
        return "Please provide a meeting title to generate preparation materials."
    
    # Increment MCP usage counter
    if actor.properties:
        actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
        
        # Get relevant notes and reminders for context
        notes = actor.properties.get("notes", [])
        reminders = actor.properties.get("reminders", [])
    else:
        notes = []
        reminders = []
    
    # Build meeting prep prompt
    prompt = f"Help me prepare for a {meeting_type} meeting titled '{meeting_title}'"
    
    if duration:
        prompt += f" scheduled for {duration}"
    
    if participants:
        prompt += f" with participants: {participants}"
    
    prompt += ". Please provide:\n\n"
    
    prompt += f"1. **Suggested Agenda Structure**: Create a time-based agenda appropriate for a {meeting_type} meeting\n"
    prompt += "2. **Key Discussion Points**: Important topics that should be covered\n"
    prompt += "3. **Preparation Checklist**: What should be prepared beforehand\n"
    prompt += "4. **Success Criteria**: How to measure if the meeting was successful\n"
    
    if key_topics:
        prompt += f"\nSpecific topics to include: {key_topics}\n"
    
    # Add context from stored information
    if notes:
        relevant_notes = [
            n for n in notes[-5:] 
            if any(word in n.get("content", "").lower() for word in meeting_title.lower().split())
        ]
        if relevant_notes:
            prompt += f"\nRelevant context from recent notes:\n"
            for note in relevant_notes:
                prompt += f"- {note.get('title', 'Untitled')}: {note.get('content', '')[:100]}...\n"
    
    if reminders:
        relevant_reminders = [r for r in reminders if not r.get("completed", False)]
        if relevant_reminders:
            prompt += f"\nOpen reminders that might be relevant:\n"
            for reminder in relevant_reminders[-3:]:
                prompt += f"- {reminder.get('title', '')}: {reminder.get('due_date', '')}\n"
    
    prompt += (
        f"\nPlease tailor the meeting preparation specifically for a {meeting_type} format with {duration} duration."
    )
    
    logger.info(f"MCP Prompt: Generated meeting prep for '{meeting_title}' ({meeting_type})")
    
    return prompt