import React, { Component } from 'react';

export class Home extends Component {
    displayName = Home.name

    constructor(props) {
        super(props); // pass to base class. 
        this.handleChange = this.handleUploadImage.bind(this);
        this.state = { imageData : "" }; 
    }

    handleUploadImage(files) {

        const data = new FormData();
        data.append('file', files[0]);
        data.append('filename', files[0].name);

        this.setState({ imageData: process.env.PUBLIC_URL + "/running.jpg" });

        fetch('https://deepgrave.me/api/upload', {
            method: 'POST',
            body: data,
        }).then((response) => {
            response.json().then((body) => {
                this.setState({ imageData : body.data }); 
            });
        });
        //fetch('https://localhost:5001/api/upload', {
        //    method: 'POST',
        //    body: data,
        //}).then((response) => {
        //    response.json().then((body) => {
        //        this.setState({ imageData: body.data });
        //    });
        //});
    }

    render() {
        let imagePreview = (<img src={process.env.PUBLIC_URL + "/placeholder.jpg"} />);

        if (this.state.imageData != "") {
            imagePreview = (<img src={this.state.imageData} />);
        }

        return (
            <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "120px" }}>Deep Grave</div>
                <div>
                    <label style={{ width: "500px" }} className="button glow-button">Upload Photo
                        <input ref={(ref) => { this.uploadInput = ref; }} id="file-upload" type="file" onChange={(e) => this.handleChange(e.target.files)} />
                    </label>
                </div>
                <div style={{ height: "15px" }} />
                <div>
                    {imagePreview}
                </div>
            </div>
        );
    }
}
