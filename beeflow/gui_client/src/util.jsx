import * as React from 'react';
import * as ReactDOM from 'react-dom';

export function Input(props) {
  let inputProps = {
    className: 'form-control',
    type: props.type,
    name: props.name,
    id: props.name,
    onChange: props.onChange,
  };
  if (props.value !== null) {
    inputProps.value = props.value;
  }
  // Manually create the input element
  let input = React.createElement('input', inputProps);
  return (
    <div className="mb-1">
      <label htmlFor={props.name} className="form-label">
        {props.label}
      </label>
      {input}
      <span className="text-danger">{props.error}</span>
    </div>
  );
}

// This is set to some value that hopefully will never be used as an option
export const selectDefaultValue = "SELECT_DEFAULT_VALUE";

export function Select(props) {
  let options = props.options
    .map(value => <option value={value}>{value}</option>);
  return (
    <div className="mb-1">
      <label htmlFor={props.name} className="form-label">
        {props.label}
      </label>
      <select
        id={props.name}
        name={props.name}
        className="form-select"
        onChange={props.onChange}>
        <option value={selectDefaultValue}>-- Select --</option>
        {options}
      </select>
      <span className="text-danger">{props.error}</span>
    </div>
  );
}
