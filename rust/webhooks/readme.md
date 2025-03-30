Teste at webhooken virker:

```bash
curl -X POST "http://127.0.0.1/webhook" -H "Content-Type: application/json" -d '{"event": "hello", "data": {"message": "Hello, world!"}}'
```
