import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_tasks_crud_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Task
        new_task = {
            "title": "API Test Task",
            "description": "Integration test task",
            "estimated_duration_minutes": 45,
            "priority": 4,
            "mandatory": True,
        }
        create_resp = await client.post("/api/v1/tasks", json=new_task)
        assert create_resp.status_code == 201
        created = create_resp.json()
        task_id = created["id"]
        assert created["title"] == "API Test Task"

        # List Tasks
        list_resp = await client.get("/api/v1/tasks")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert any(t["id"] == task_id for t in items)

        # Update Task
        patch_resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"priority": 5})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["priority"] == 5

        # Delete Task
        del_resp = await client.delete(f"/api/v1/tasks/{task_id}")
        assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_evaluation_benchmark_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/evaluation/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "method_summary" in data
        assert "Method C (AURA Hybrid Utility-Aware)" in data["method_summary"]
