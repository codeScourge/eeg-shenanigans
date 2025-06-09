def softmax(x):
    exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=1, keepdims=True)



def find_closest_timestamp_index(timestamps:list, target_timestamp):
    """
    Finds the index of the closest timestamp to the target timestamp.
    Uses binary search for efficiency.
    
    Args:
        timestamps: List of timestamps (assumed to be sorted)
        target_timestamp: The timestamp to find
        
    Returns:
        Index of the closest timestamp
    """
    if not timestamps:
        raise ValueError("Empty timestamps list")
    
    # Binary search for the closest value
    left, right = 0, len(timestamps) - 1
    
    # Handle edge cases
    if target_timestamp <= timestamps[0]:
        return 0
    if target_timestamp >= timestamps[-1]:
        print(f"timestep {target_timestamp} received from frontend, is bigger than the latest timestamp {timestamps[-1]}")
        return len(timestamps) - 1
    
    # Binary search
    while left <= right:
        mid = (left + right) // 2
        
        if timestamps[mid] == target_timestamp:
            return mid
        
        if timestamps[mid] < target_timestamp:
            left = mid + 1
        else:
            right = mid - 1
    
    # At this point, left > right
    # Return the closest of timestamps[right] and timestamps[left]
    if left >= len(timestamps):
        return right
    if right < 0:
        return left
        
    if abs(timestamps[right] - target_timestamp) < abs(timestamps[left] - target_timestamp):
        return right
    else:
        return left