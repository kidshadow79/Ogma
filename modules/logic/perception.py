import queue

async def get_visual_events_context(perception_agent):
    """
    Extraction du contexte visuel depuis l'agent de perception.
    
    Args:
        perception_agent: Agent perception avec event_queue
        
    Returns:
        str: Contexte visuel formaté
    """
    visual_events = ""
    events_to_requeue = []
    
    if not hasattr(perception_agent, 'event_queue'):
        return ""
        
    while not perception_agent.event_queue.empty():
        try:
            event = perception_agent.event_queue.get_nowait()
            if "[EVENT]" in event:
                visual_events += f"- {event.replace('[EVENT]', '').strip()}\n"
            else:
                events_to_requeue.append(event)
        except queue.Empty:
            break
    
    # Remettre en queue les événements non-visuels
    for item in events_to_requeue:
        perception_agent.event_queue.put(item)
    
    if visual_events:
        return f"Contexte visuel perçu :\n{visual_events}"
    return ""
