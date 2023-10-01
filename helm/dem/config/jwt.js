function jwt(data) {
  if (data) {
    var parts = data
      .split('.')
      .slice(0, 2)
      .map(v => Buffer.from(v, 'base64url').toString())
      .map(JSON.parse);
    return { headers: parts[0], payload: parts[1] };
  } else {
    return;
  }
}

function jwt_payload_sub(r) {
  try {
    let token;
    if (r.args['token']) {
      token = jwt(r.args['token']);
      if (!token) {
        return '';
      }
      return token.payload.sub;
    }
    if (r.headersIn['x-api-key']) {
      token = jwt(r.headersIn['x-api-key']);
      if (!token) {
        return '';
      }
      return token.payload.sub;
    }
    return '';
  } catch (error) {
    return '';
  }
}

export default { jwt_payload_sub };
