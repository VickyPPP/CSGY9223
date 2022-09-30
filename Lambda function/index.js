exports.handler = async (event) => {
    // TODO implement
    const response = {
        statusCode: 200,
        headers: {
            "Access-Control-Allow-Headers" : "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        
        "messages": [
          {
            "type": "unstructured",
            "unstructured": {
              "id": Date.now(),
              "text": "Application under development. Search functionality will be implemented in Assignment 2",
              "timestamp": Date.now()
            }
          }
        ],
    };
    
    return response;
};