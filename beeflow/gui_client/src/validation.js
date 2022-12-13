// Validation code
import * as React from 'react';
import {selectDefaultValue} from './util.jsx'

export class ValidatedForm extends React.Component {
  constructor(props) {
    super(props);
  }

  handleInputChange(ev) {
    const target = ev.target;
    this.setState({
      [target.name]: target.value,
    })
    console.log(this.state)
  }

  handleChangeRegex(ev, re, label, name) {
    const target = ev.target;
    let value = target.value;
    if (!re.test(value)) {
      let errors = this.state.errors;
      errors[name] = `${label} is invalid`;
      this.setState({errors});
      return;
    }
    // It passed, so delete any errors and set the input value
    let errors = this.state.errors;
    delete errors[name];
    this.setState({
      [name]: target.value,
      errors,
    })
  }

  // Handle a change in a file input
  handleChangeFile(ev, fnameRegex, name) {
    const target = ev.target;
    let file = target.files[0];
    console.log(file.name);
    if (!fnameRegex.test(file.name)) {
      let errors = this.state.errors;
      errors[name] = `"${file.name}" is an invalid file name`;
      this.setState({errors});
      return;
    }
    let errors = this.state.errors;
    delete errors[name];
    this.setState({errors});
    target.files[0].arrayBuffer()
      .then(data => {
        this.setState({
          [name]: data,
        })
      })
      .catch(err => alert(err));
  }

  handleChangeSelect(ev, label, name) {
    const target = ev.target;
    console.log(target.value);
    if (target.value == selectDefaultValue) {
      let errors = this.state.errors;
      errors[name] = `You must select an option for ${label}`;
      this.setState({errors});
      return;
    }
    let errors = this.state.errors;
    delete errors[name];
    this.setState({
      [name]: target.value,
      errors,
    });
  }

  // Validate all fields if missing. If everything passes, then execute the
  // callback with final data.
  validateAll(fields, labels, callback) {
    if (fields.some(field => Object.hasOwn(this.state.errors, field))
        || !fields.every(field => Object.hasOwn(this.state, field))) {
      // There are empty fields, so we need to show errors for each
      let emptyFieldErrors = fields
        .filter(field => !Object.hasOwn(this.state, field))
        .map(field => {
          let i = fields.indexOf(field);
          return [field, `${labels[i]} cannot be empty`]
        });
      let errors = {...this.state.errors};
      Object.assign(errors, Object.fromEntries(emptyFieldErrors));
      this.setState({errors});
      return;
    }
    // No error and no fields were empty, so create the cluster config
    this.setState({errors: {}});
    let data = Object.fromEntries(fields.map(field => [field, this.state[field]]));
    // TODO: Make this into a promise
    callback(data);
  }
}
