def detect_device_type(user_agent: str) -> str:
    ua = user_agent.lower()

    if "iphone" in ua or "ipad" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    if "mobile" in ua:
        return "mobile"
    return "desktop"
