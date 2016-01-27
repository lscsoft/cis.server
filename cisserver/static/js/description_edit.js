function editdescription(divid, pk) {
    // console.info("DOING EDIT");
    dojo.xhrGet({
        url: edit_description_url(pk),
        //"{% url edit_description 0 %}"+pk,
        load: function(result) {
            // console.info("RESULT: " + result);
            dojo.byId(divid).innerHTML = result;
        },
        error: function(errorMessage) {
            console.info("ERROR: " + errorMessage);
        }
    });
    // console.info("DONE EDIT");
}
function savedescription(divid, formid, pk) {
    // console.info("DOING SAVE");
    dojo.xhrPost({
        url: edit_description_url(pk),
        //"{% url edit_description 0 %}"+pk,
        form: dojo.byId(formid),
        load: function(result) {
            // console.info("SAVE RESULT: " + result);
            dojo.byId(divid).innerHTML = result;
        },
        error: function(errorMessage) {
            // console.info("SAVE ERROR: " + errorMessage);
            dojo.byId(divid).innerHTML = errorMessage;
        }
    });
    // console.info("DONE SAVE");
}
function canceldescription(divid, pk) {
    // console.info("DOING Cancel");
    dojo.xhrGet({
        url: edit_description_url(pk)+"?cancel",
        //"{% url edit_description 0 %}"+pk+"?cancel",
        load: function(result) {
            // console.info("RESULT: " + result);
            dojo.byId(divid).innerHTML = result;
        },
        error: function(errorMessage) {
            console.info("ERROR: " + errorMessage);
        }
    });
    // console.info("DONE Cancel");
}
