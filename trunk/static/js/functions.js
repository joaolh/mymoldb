function get_mol_info() {
    var smiles = JSDraw.get("moleditor").getSmiles();
    var mol = JSDraw.get("moleditor").getMolfile();
    var slct = document.form1.dbchoose;
    if (smiles!=null) {
        document.form1.smiles.value = smiles;
        document.form1.mol.value = mol;
        document.form1.db.value = slct.options[slct.selectedIndex].value;
        var info = document.referrer;
        info += " - " + navigator.appName + " - " + navigator.appVersion;
        info += " " + screen.width + "x" + screen.height;
        document.form1.info.value = info;
        document.form1.submit();
    } else {
        alert("no molecular structure to search!");
    }
}
function SendMessage(){
    var form = document.getElementById('login_form');
    if (form.username.value=="") {
        alert("empty user name entry!");
    } else if(form.password.value=="") {
        alert("empty pass word entrt!");
    } else {
        form.submit();
    }
}

