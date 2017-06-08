import axios      from 'axios'

import config     from '../Config'
import ActionType from '../constant/ActionType'

const insertRow    = (row) => {
  const action     = {
       type: ActionType.INSERT_ROW,
    payload: row
  }

  return action
}

const insertColumn = (column) => {
  const action     = {
       type: ActionType.INSERT_COLUMN,
    payload: column
  }

  return action
}

const updateRows   = (fromRow, toRow, update) => {
  const action     = {
       type: ActionType.UPDATE_ROWS,
    payload: {
      fromRow: fromRow,
        toRow: toRow,
       update: update
    }
  }

  return action
}

const refreshData  = (dispatch) => {
  dispatch(refreshDataRequest())
  axios.post(config.routes.files)
       .then((response) => {
         response = response.data

         if ( response.status == "success" ) {
           const data   = response.data
           const action = refreshDataSuccess(data)

           dispatch(action)
         } else {
           // TODO: handle fail, error
         }
       })
}

const refreshDataRequest = () => {
  const action           = {
    type: ActionType.REFRESH_DATA_REQUEST
  }

  return action
}

const refreshDataSuccess = (data) => {
  const action           = {
       type: ActionType.REFRESH_DATA_SUCCESS,
    payload: data
  }

  return action
}

export { insertRow, insertColumn, updateRows, refreshData }
