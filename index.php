<?php

    $short_hash = shell_exec('git rev-parse --short HEAD');

    if (!empty($_GET['page'])) {
        $page = $_GET['page'];
    } else {
        $page = "home";
    }

    function Redirect($url, $permanent = false) {
        header('Location: ' . $url, true, $permanent ? 301 : 302);
        exit();
    }

    /**
     * Function: sanitize
     * Returns a sanitized string, typically for URLs.
     *
     * Parameters:
     *     $string - The string to sanitize.
     *     $force_lowercase - Force the string to lowercase?
     *     $anal - If set to *true*, will remove all non-alphanumeric characters.
     */
    function sanitize($string, $force_lowercase = true, $anal = false) {
        $strip = array("~", "`", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "=", "+", "[", "{", "]",
                    "}", "\\", "|", ";", ":", "\"", "'", "&#8216;", "&#8217;", "&#8220;", "&#8221;", "&#8211;", "&#8212;",
                    "â€”", "â€“", ",", "<", ".", ">", "/", "?");
        $clean = trim(str_replace($strip, "", strip_tags($string)));
        $clean = preg_replace('/\s+/', "_", $clean);
        $clean = ($anal) ? preg_replace("/[^a-zA-Z0-9]/", "", $clean) : $clean ;
        return ($force_lowercase) ?
            (function_exists('mb_strtolower')) ?
                mb_strtolower($clean, 'UTF-8') :
                strtolower($clean) :
            $clean;
    }

    if (!empty($_POST['redirect'])) {
        $redirect = $_POST['redirect'];
    } else {
        $redirect = "FALSE";
    }

    if ($page === "config" or $page === "setup" or $page === "edit") {
        $page = "$page/1";
    }

    if ($redirect !== "TRUE") {
        include "php/header.html"; ?>
        <div class="content">
            <h1><a href="/">LooPyGen UI</a> ( <?php echo $short_hash ?>)</h1>
            <?php include "php/$page.php"; ?>
        </div>
    <?php } else {
        include "php/$page.php";
    }

    include "php/footer.html";

?>