<?php

    $collection = $_GET['collection'];
    $new_traits_file = file_get_contents("./collections/${collection}/config/traits.tmp.json");
    $new_traits = json_decode($new_traits_file, true);
    $collection_lower = $new_traits['collection_lower'];

    if ($collection === $collection_lower) {    // Collection stays in same directory
        rename("./collections/${collection}/config/traits.tmp.json", "./collections/${collection}/config/traits.json");
    }
    else {  // Collection directory needs to change
        /**
         * Copy a file, or recursively copy a folder and its contents
         *
         * @author      Aidan Lister <aidan@php.net>
         * @version     1.0.1
         * @link        http://aidanlister.com/2004/04/recursively-copying-directories-in-php/
         * @param       string   $source    Source path
         * @param       string   $dest      Destination path
         * @return      bool     Returns TRUE on success, FALSE on failure
         */
        function copyr($source, $dest)
        {
            // Check for symlinks

            if (is_link($source)) {
                return symlink(readlink($source), $dest);
            }

            // Simple copy for a file

            if (is_file($source)) {
                return copy($source, $dest);
            }

            // Make destination directory

            if (!is_dir($dest)) {
                mkdir($dest);
            }

            // Loop through the folder

            $dir = dir($source);
            while (false !== $entry = $dir->read()) {
                // Skip pointers

                if ($entry == '.' || $entry == '..') {
                    continue;
                }

                // Deep copy directories

                copyr("$source/$entry", "$dest/$entry");
            }

            // Clean up

            $dir->close();
            return true;
        }

        copyr("./collections/${collection}", "./collections/${collection_lower}");   // Copy all files to the new collections directory
        rename("./collections/${collection_lower}/config/traits.tmp.json", "./collections/${collection_lower}/config/traits.json");   // Move temporary json to permanent traits.json
        system("rm -rf ".escapeshellarg("./collections/${collection}")); // Remove old collections directory

    }

    $s = 1;
    $t_display = $new_traits['trait_count'];

    if (!empty($new_traits)) {
        ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <section>
                <p><b>Collection Name</b>: <?php echo $new_traits['collection_name'] ?></p>
                <?php if (array_key_exists('artist_name', $new_traits)) {
                    echo "<p><b>Artist's Name</b>: " . $new_traits['artist_name'] . "</p>";
                } ?>
                <?php if (array_key_exists('royalty_address', $new_traits)) {
                    echo "<p><b>Royalty Address</b>: " . $new_traits['royalty_address'] . "</p>";
                } ?>
                <?php if ($new_traits['background_color'] === true) {
                    echo "<p><b>Generate Background Colors</b>: YES</p>";
                    $s = 0;
                    $t_display = $t_display + 1;
                } ?>
                <p><b>Total Traits</b>: <?php echo $t_display ?></p>
            </section>
        </div>
        <div class="nav">
            <a href="/collection/images?collection=<?php echo $collection_lower ?>">GENERATE IMAGES</a>
            <a href="/home">MAIN MENU</a>
        </div>
    <?php } else {
        Redirect('/setup/1', false);
    }

?>