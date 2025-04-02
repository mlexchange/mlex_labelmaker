import asyncio
import os

from mlex_utils.prefect_utils.core import get_children_flow_run_ids
from prefect import get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterName,
    FlowRunFilterParentFlowRunId,
    FlowRunFilterState,
    FlowRunFilterStateType,
    FlowRunFilterTags,
)
from prefect.client.schemas.objects import StateType

FLOW_NAME = os.getenv("FLOW_NAME")
USER = os.getenv("USER")


# TODO: Add to mlex_utils
async def _flow_run_query(
    tags=None,
    flow_run_name=None,
    parent_flow_run_id=None,
    state=None,
    sort="START_TIME_DESC",
):
    flow_run_filter_parent_flow_run_id = (
        FlowRunFilterParentFlowRunId(any_=[parent_flow_run_id])
        if parent_flow_run_id
        else None
    )
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(
            flow_run_filter=FlowRunFilter(
                name=FlowRunFilterName(like_=flow_run_name),
                parent_flow_run_id=flow_run_filter_parent_flow_run_id,
                tags=FlowRunFilterTags(all_=tags),
                state=FlowRunFilterState(type=FlowRunFilterStateType(any_=state)),
            ),
            sort=sort,
        )
        return flow_runs


def query_flow_runs(flow_name, tags=None, state=None):
    """
    This function queries the flow runs
    Args:
        flow_name:          Flow name
        tags:               Tags
        state:              State
    Returns:
        flow_runs:          Flow runs
    """
    flow_runs = asyncio.run(
        _flow_run_query(tags=tags, flow_run_name=flow_name, state=state)
    )
    return flow_runs


def get_trained_models_list(user, similarity=True, project_name=None):
    """
    This function queries the MLCoach or DataClinic results
    Args:
        user:               Username
        similarity:         [Bool] Retrieve f_vec vs probabilities
        project_name:       Project name
    Returns:
        trained_models:     List of options
    """
    flow_runs = []
    if similarity:
        flow_runs += query_flow_runs(
            FLOW_NAME,
            tags=["data-clinic", project_name, "train"],
            state=[StateType.COMPLETED],
        )
        flow_runs += query_flow_runs(
            FLOW_NAME,
            tags=["data-clinic", project_name, "inference"],
            state=[StateType.COMPLETED],
        )
    flow_runs += query_flow_runs(
        FLOW_NAME,
        tags=["mlcoach", project_name, "inference"],
        state=[StateType.COMPLETED],
    )

    trained_models = []
    for flow_run in flow_runs:
        children_flow_run_ids = get_children_flow_run_ids(flow_run.id)
        if "train" in flow_run.tags:
            job_id = children_flow_run_ids[1]
        else:
            job_id = children_flow_run_ids[0]

        # TODO: Modify path to f"/{USER}/{project_name}/feature_vectors/{job_id}"
        trained_models.append(
            {
                "label": flow_run.name,
                "value": f"/{USER}/{project_name}/{job_id}/feature_vectors",
            }
        )
    return trained_models
